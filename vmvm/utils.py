def disk_image_format_by_name(filename: str) -> str:
    return 'qcow2' if 'qcow2' in filename else 'raw'
