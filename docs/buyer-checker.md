# Buyer Checker implementation context

Seller Guard has a [React and Vite reviewer demo](../web/seller-guard/README.md)
with an overview and a reviewer queue. Add a buyer-facing check for a specific
Shopee listing and variation. Use the prepared demo dataset and reuse the
[U3 rules](../src/trongpok/rules.py) and [shared record shapes](../src/trongpok/shapes.py).
Keep the existing reviewer workflow available alongside the buyer flow.

## Buyer experience

Use the Review Check **Store Check** flow as the UX reference. Its useful
pattern is a single product-link field and a **Start check** button, followed
by a confirmation step and a result screen that leads with the finding.

1. **Find a listing.** Accept a Shopee product link. Offer title search as a
   secondary option. If the dataset has several matches, show the listing
   names and shops so the buyer can choose.
2. **Confirm the variation.** Show the shop, listing, and available options.
   Pass the confirmed `listing_id` and `option_id` to the result flow.
3. **Show the finding and evidence.** Lead with the selected option and the
   strongest reason. Use plain-language findings such as **Capacity concern**,
   **Price unusually low**, **Capacity differs from manufacturer specs**,
   **Insufficient evidence**, and **No concerns found in the available evidence**.
   Let buyers inspect the supporting review quotes, price sources, or
   manufacturer specifications. Show any relevant evidence gaps.
4. **Let the buyer decide what to do.** Where relevant, provide a copyable,
   listing-specific explanation and an **Open Shopee to report** action. The
   buyer reviews and submits the report in Shopee's product reporting flow.

A shop overview can group completed results by shop and show how many options
were assessed. Use wording such as **2 of 5 assessed options need review**.

## Four workstreams

| Issue | Deliverable |
| --- | --- |
| [#18 · Demo data and evidence](https://github.com/Boomudm/Sea-X-OpenAI/issues/18) | Labeled records with shop, listing, exact variations, and the available review, manufacturer, and price evidence. Share one complete example first. |
| [#19 · Listing lookup and variation selection](https://github.com/Boomudm/Sea-X-OpenAI/issues/19) | URL lookup and title search against the demo dataset, with candidate selection and exact option IDs. |
| [#20 · U3 rules and buyer results](https://github.com/Boomudm/Sea-X-OpenAI/issues/20) | A buyer result for the selected option with a finding, reason, sources, and a report explanation where relevant. |
| [#21 · Buyer web flow and deployment](https://github.com/Boomudm/Sea-X-OpenAI/issues/21) | A deployed site that connects lookup, confirmation, evidence, and the Shopee reporting handoff. |

Check issue ownership before starting and follow the repository's
[working agreement](../AGENTS.md). Start with one shared example so the lookup,
result mapping, and UI can progress in parallel. The first release reads
prepared data. Live lookup is a follow-up once approved access supplies the
listing, variation, and review fields.

## Demo acceptance

A teammate can open the deployed URL on a second device and complete the flow.
Verify four clearly labeled examples:

- Two independent buyers report 29–30.5 GB for the same 64 GB option. The
  result shows a capacity concern with the exact supporting evidence.
- A normal 58 GB display reading on a 64 GB drive does not raise a capacity
  concern after GB/GiB normalization.
- An option with an unusually low price shows the price comparison and a
  price-specific finding.
- A listing with limited evidence shows what is missing.

Also verify that an ambiguous title offers a choice and that a listing
outside the demo dataset gets a clear unavailable message.
