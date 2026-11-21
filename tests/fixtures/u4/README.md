# Sample reviewer queue

Every listing, buyer, measurement, rating, price and source here is synthetic.
These files exercise the reviewer UI without making marketplace claims.
The sample source URLs use the reserved `example.invalid` domain.

| Sample | Option | Expected result |
| --- | --- | --- |
| Compact | 64 GB | RED, four independent shortfall quotes despite ฿224 and 4.8 stars |
| Standard | 64 GB | GREEN, ten checked reviews including a normal 58 GB reading |
| Discount | 1 TB | RED, ฿299 against a ฿1,800–2,400 range |
| Reference | 1 TB · Black | GREY, ฿2,000 inside the range despite ฿6,000 crossed out, with no buyer data |
| Reference | 1 TB · Blue | YELLOW, ฿1,500 with ฿2,000 crossed out |

The rating is a sample listing-level value in its captured specifications.
It is independent of the four selected review excerpts. This sample contains
text-only buyer evidence.

Regenerate the saved captures and U3 flags from the repository root:

```sh
uv run python tests/fixtures/u4/build.py
```
