import json

import pytest

from src.lib.schemas import TaxonomyIn
from src.utils.wp_utils import wp_batch_get_or_add_terms, wp_get_or_create_user
from tests import FILES_DIR


def test_wp_batch_get_or_add_terms_4_category():
    translations = TaxonomyIn(**json.loads(FILES_DIR.joinpath("jsons/category_translations.json").read_text()))
    result = wp_batch_get_or_add_terms(translations)
    assert len(result) == 14
    assert len(result["en"]) == 3
    for term_id in result["en"]:
        assert isinstance(term_id, int)


def test_wp_batch_get_or_add_terms_4_tag():
    translations = TaxonomyIn(**json.loads(FILES_DIR.joinpath("jsons/tag_translations.json").read_text()))
    result = wp_batch_get_or_add_terms(translations)
    assert len(result) == 14
    assert len(result["en"]) == 4
    for term_id in result["en"]:
        assert isinstance(term_id, int)


@pytest.mark.parametrize("name, url", [
    ("The name", "   "),
    ("", "https://www.youtube.com/profile/fullu/"),
    ("Moon Cresta", "https://www.youtube.com/profile/MoonCresta/"),
    ("javhd", "https://www.vdieohub.com/channels/javhd"),
    ("lilyxoxoles", "https://www.good.com/model/lilyxoxoles"),
    ("lilyxoxoles", "https://news.com/model/lilyxoxoles"),
    ("what is@👌", "https://news.com/model/tummy"),
])
def test_wp_custom_get_or_create_user(name, url):
    assert isinstance(wp_get_or_create_user(name, url), int)
