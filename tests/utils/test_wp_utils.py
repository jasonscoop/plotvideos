import json

from src.lib.schemas import TaxonomyIn
from src.utils.wp_utils import wp_batch_get_or_add_terms
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
