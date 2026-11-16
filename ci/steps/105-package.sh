args=(--os "$OS_PROFILE" --uefi ../uefi-sheng)
if [ "$OS_PROFILE" = 27 ] && [ "$INIT_DATA" = true ]; then
  args+=(--init-data)
fi
scripts/package.sh "${args[@]}"
