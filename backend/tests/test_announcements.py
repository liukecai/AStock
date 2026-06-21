from app.services.announcements import _announcement_id, _normalize_time


def test_cninfo_announcement_id_prefers_official_id():
    url = (
        "https://www.cninfo.com.cn/new/disclosure/detail?"
        "stockCode=300750&announcementId=1225378102"
    )
    assert (
        _announcement_id(url, "300750", "公告", "2026-06-18")
        == "cninfo:1225378102:300750"
    )


def test_cninfo_time_normalization():
    assert _normalize_time("2026-06-18") == "2026-06-18T00:00:00"
    assert _normalize_time("2026-06-18 17:22:10") == "2026-06-18T17:22:10"
