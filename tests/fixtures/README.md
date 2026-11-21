# Synthetic integration fixture

All values in this folder are synthetic. The listing has four distinct buyers
of the same 64 GB option. Their matched review findings should produce one RED
flag whose deciding reason is Q3. The fixture contains no market data.

- `listing.json` is the captured-listing shape.
- `findings.json` is the reader findings shape.
- `flags.json` is the expected rules output shape for the reviewer queue.
