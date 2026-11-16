if ! [[ "$seed" =~ ^[0-9a-fA-F]{8}$ ]]; then
  echo 'Set the repository secret UNIXNU_UNIQUE_CHIP_ID: the platform seed of the device, 8 hex digits.' >&2
  exit 1
fi
