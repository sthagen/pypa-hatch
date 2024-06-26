import hashlib
import os
import tempfile

from hatchling.builders.utils import format_file_hash, normalize_artifact_permissions


def update_record_file_contents(record_file, files, generated_files=()):
    for template_file in sorted(
        files,
        key=lambda f: (
            f.path.parts[0].endswith('.dist-info'),
            f.path.parts[0].endswith('.dist-info') and f.path.parts[1] == 'extra_metadata',
            f.path.parts[0].startswith('z'),
            len(f.path.parts),
            f.path.parts,
        ),
    ):
        if isinstance(template_file.contents, bytes):
            is_binary = True
            raw_contents = template_file.contents
        else:
            is_binary = False
            raw_contents = template_file.contents.encode('utf-8')

        template_file_path = str(template_file.path)
        if (
            not is_binary
            and os.linesep != '\n'
            and (
                'LICENSE' in template_file_path
                or (
                    not template_file.path.parts[0].endswith('.dist-info')
                    and all(f not in template_file_path for f in generated_files)
                )
            )
        ):
            raw_contents = raw_contents.replace(b'\n', b'\r\n')

        hash_obj = hashlib.sha256()
        hash_obj.update(raw_contents)
        hash_digest = format_file_hash(hash_obj.digest())
        record_file.contents += f'{template_file.path.as_posix()},sha256={hash_digest},{len(raw_contents)}\n'

    record_file.contents += f'{record_file.path.as_posix()},,\n'


def test_normalize_artifact_permissions():
    """
    assert that this func does what we expect on a tmpfile that that starts at 600
    """
    _, path = tempfile.mkstemp()

    file_stat = os.stat(path)
    assert file_stat.st_mode == 0o100600

    normalize_artifact_permissions(path)

    file_stat = os.stat(path)
    assert file_stat.st_mode == 0o100644
