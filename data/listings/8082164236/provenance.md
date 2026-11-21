# READY 2TB capture

The original Shopee capture was made on 21 November 2026 at approximately 13:43 ICT. The exact `2TB` option showed ฿259 before personal coupons. No crossed-out price was visible. Other variants were outside this capture. `spec_text` summarizes the displayed specifications. Shopee displayed a listing-wide rating of 4.6, 1.8k reviews and 5k+ sold. [Listing](https://shopee.co.th/product/347855549/8082164236)

The capture retained two review rows from the visible `1 ดาว (85)` (one-star) filter. The original capture inspected the first six pages, totaling 36 ratings, and selected these two rows for their exact Variation and capacity statements. The capture is a selected subset. Counts and page positions describe the capture session.

| Local review ID | Position in the one-star filter | Masked buyer | Displayed date and time (ICT) | Variation |
| --- | --- | --- | --- | --- |
| `8082164236-r01` | Page 2, row 3 of 6 | `n*****k` | 2023-09-07 12:01 | `2TB` |
| `8082164236-r02` | Page 6, row 2 of 6 | `a*****s` | 2022-02-17 10:19 | `2TB` |

Both review IDs and the option ID `8082164236-option-2tb` are local identifiers. Shopee review IDs were unavailable. Both texts and positions were verified against saved snapshots of the visible Shopee page. No complaint tags or buyer photos or videos were shown for these rows. The original displayed layouts supplied the buyer text in the adjacent listing JSON.

`images/listing-01.webp` is the Shopee listing image saved through the visible product-image control. It decodes as 800 × 800 pixels. The image shows the drive and promotional art. The pixels and embedded image metadata contain no shipping label or personal data. SHA-256 `69c1f84fa79e7ee12269a0fbddfcc8abf2980513aa622cb4c5f52e1c80d63c57`. [Shopee image source](https://down-th.img.susercontent.com/file/sg-11134201-7rdwy-lyyznlv5w7pjd0)

## Offline replay

The findings in `out/findings/22165813567.json` and `out/findings/8082164236.json` were manually normalized from source-checked review text. The replay uses these saved inputs and runs without an API key. For the two captured options, run from the repository root.

```sh
uv run --locked trongpok-analyze data/listings/22165813567.json data/listings/8082164236.json
```

The SanDisk option is GREEN (Q5) with 22 matched and checked text reviews. The READY option is YELLOW (Q4). One buyer reports 20 GB. The other describes a little over 10 GB without a precise amount, so the manual finding records a capacity complaint without a usable measurement. Both options retain an unsure verdict until a reviewer decides.

To regenerate the local Seller Guard data and build the web app, run the following from the repository root.

```sh
uv run --locked python -m trongpok.export_web
cd web/seller-guard
npm ci --no-audit --no-fund
npm run build
```
