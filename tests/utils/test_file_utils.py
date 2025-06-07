from src.utils.file_utils import upload_dir_to_s3
from tests import SUBTITLES_DIR


def test_upload_dir_to_s3():
    assert upload_dir_to_s3(SUBTITLES_DIR, "000_a_test_upload_dir_to_s3")
