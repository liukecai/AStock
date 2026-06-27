import os
import glob
import yaml
import hashlib
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert

# Ensure we can import app modules if run as script
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.config import settings
from app.models.v2_kg import KGEntity, KGRelation
from app.pg_dsn import resolve_pg_dsn

def _md5_id(entity_type: str, name: str) -> str:
    return hashlib.md5(f"{entity_type}:{name}".encode('utf-8')).hexdigest()

def _md5_rel_id(src: str, rel_type: str, tgt: str) -> str:
    return hashlib.md5(f"{src}:{rel_type}:{tgt}".encode('utf-8')).hexdigest()


def _resolve_db_url() -> str:
    return resolve_pg_dsn(settings.database_url)

def load_yaml_to_kg():
    # Setup DB
    db_url = _resolve_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Find YAMLs
    yaml_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "config", "commodity_graph")
    yaml_files = glob.glob(os.path.join(yaml_dir, "*.yaml"))

    now = datetime.now()
    entities_upserted = 0
    relations_upserted = 0

    try:
        for yf in yaml_files:
            with open(yf, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'commodity' not in data:
                continue

            commodity_key = data['commodity']
            commodity_name = data.get('name', commodity_key)

            # 1. Upsert Commodity Entity
            comm_id = _md5_id("Commodity", commodity_name)
            comm_stmt = insert(KGEntity).values(
                entity_id=comm_id,
                entity_type="Commodity",
                name=commodity_name,
                canonical_name=commodity_name,
                aliases_json=data.get('keywords', []),
                description=f"Commodity {commodity_name}",
                metadata_json={"yaml_key": commodity_key},
                status="active",
                created_at=now,
                updated_at=now
            ).on_conflict_do_update(
                index_elements=['entity_id'],
                set_={
                    'aliases_json': data.get('keywords', []),
                    'updated_at': now
                }
            )
            session.execute(comm_stmt)
            entities_upserted += 1

            # 2. Upsert Sectors
            sectors = set(data.get('upstream_sectors', []) + data.get('downstream_sectors', []) + data.get('sector_keywords', []))
            for sec in sectors:
                sec_id = _md5_id("Sector", sec)
                sec_stmt = insert(KGEntity).values(
                    entity_id=sec_id,
                    entity_type="Sector",
                    name=sec,
                    canonical_name=sec,
                    aliases_json=[],
                    description=f"Sector {sec}",
                    metadata_json={},
                    status="active",
                    created_at=now,
                    updated_at=now
                ).on_conflict_do_update(
                    index_elements=['entity_id'],
                    set_={'updated_at': now}
                )
                session.execute(sec_stmt)
                entities_upserted += 1

                # Commodity -> Sector Relation (simplified to belongs_to)
                rel_id = _md5_rel_id(comm_id, "belongs_to", sec_id)
                rel_stmt = insert(KGRelation).values(
                    relation_id=rel_id,
                    source_entity_id=comm_id,
                    target_entity_id=sec_id,
                    relation_type="belongs_to",
                    direction="directed",
                    weight=1.0,
                    confidence=1.0,
                    source_type="yaml_seed",
                    status="active",
                    created_at=now,
                    updated_at=now
                ).on_conflict_do_update(
                    index_elements=['relation_id'],
                    set_={'updated_at': now}
                )
                session.execute(rel_stmt)
                relations_upserted += 1

            # 3. Upsert Exact Stocks
            exact_stocks = data.get('exact_stocks', {})
            for symbol, stock_info in exact_stocks.items():
                stock_name = stock_info.get('name', symbol)
                comp_id = _md5_id("Company", stock_name)
                comp_stmt = insert(KGEntity).values(
                    entity_id=comp_id,
                    entity_type="Company",
                    name=stock_name,
                    canonical_name=stock_name,
                    aliases_json=[symbol],
                    description=f"Company {stock_name} ({symbol})",
                    metadata_json={"stock_code": symbol},
                    status="active",
                    created_at=now,
                    updated_at=now
                ).on_conflict_do_update(
                    index_elements=['entity_id'],
                    set_={'updated_at': now, 'metadata_json': {"stock_code": symbol}}
                )
                session.execute(comp_stmt)
                entities_upserted += 1

                # Relation: Company -> Commodity
                relationship = stock_info.get('relationship', 'upstream')
                rel_type = "produces" if relationship == 'upstream' else "uses"
                
                rel_id = _md5_rel_id(comp_id, rel_type, comm_id)
                rel_stmt = insert(KGRelation).values(
                    relation_id=rel_id,
                    source_entity_id=comp_id,
                    target_entity_id=comm_id,
                    relation_type=rel_type,
                    direction="directed",
                    weight=1.0,
                    confidence=1.0,
                    source_type="yaml_seed",
                    status="active",
                    created_at=now,
                    updated_at=now
                ).on_conflict_do_update(
                    index_elements=['relation_id'],
                    set_={'updated_at': now}
                )
                session.execute(rel_stmt)
                relations_upserted += 1

        session.commit()
        print(f"✅ Successfully processed {len(yaml_files)} YAML files.")
        print(f"✅ Upserted {entities_upserted} Entities and {relations_upserted} Relations.")
    except Exception as e:
        session.rollback()
        print(f"❌ Error loading YAMLs: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    load_yaml_to_kg()
