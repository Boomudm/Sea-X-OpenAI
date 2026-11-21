"""A keyboard-accessible Streamlit table that opens the selected option."""

import streamlit as st

option_table = st.components.v2.component(
    "review_options",
    html="""
        <div class="review-table">
          <table aria-label="Options to review">
            <colgroup><col style="width:34%"><col style="width:13%">
              <col style="width:29%"><col style="width:13%"><col style="width:11%"></colgroup>
            <thead><tr>
              <th scope="col">Listing</th><th scope="col">Option</th>
              <th scope="col">Priority</th><th scope="col">Confidence</th><th scope="col">Verdict</th>
            </tr></thead>
            <tbody></tbody>
          </table>
        </div>
    """,
    css="""
        .review-table {
            max-height: 28rem;
            overflow: auto;
            border: 1px solid var(--st-border-color);
            border-radius: .75rem;
        }
        table { border-collapse: separate; border-spacing: 0; table-layout: fixed; width: 100%; }
        thead { position: sticky; top: 0; z-index: 1; }
        th, td { padding: .55rem .75rem; overflow-wrap: anywhere; text-align: left; }
        th { background: var(--st-secondary-background-color); font-weight: 650; }
        td { border-top: 1px solid var(--st-border-color); }
        tbody tr { cursor: pointer; }
        tbody tr:hover, tbody tr:focus-within { background: var(--st-secondary-background-color); }
        button {
            border: 0; border-radius: .25rem; background: transparent; color: inherit;
            font: inherit; font-weight: 650; min-height: 2.75rem; padding: 0;
            text-align: left; cursor: pointer;
        }
        button:hover { text-decoration: underline; }
        button:focus-visible { outline: 2px solid var(--st-primary-color); outline-offset: 3px; }
        .priority {
            display: inline-flex; align-items: center; gap: .45rem;
            color: var(--st-text-color); font-weight: 600;
        }
        .priority::before {
            content: ""; width: .58rem; height: .58rem; flex: 0 0 .58rem;
            border-radius: 50%; background: var(--priority-color);
        }
        .red { --priority-color: #d84236; }
        .yellow { --priority-color: #c68419; }
        .grey { --priority-color: #85858c; }
        .green { --priority-color: #25826a; }
        .score { font-variant-numeric: tabular-nums; font-weight: 650; }
        @media (max-width: 45rem) {
            table, thead, tbody { display: block; }
            thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
            tbody tr { display: grid; grid-template-columns: 1fr 1fr; padding: .55rem .75rem; }
            tbody tr + tr { border-top: 1px solid var(--st-border-color); }
            td { border: 0; padding: .2rem .5rem .2rem 0; }
            td:first-child { grid-column: 1 / -1; }
            .score::after { content: " confidence"; font-weight: 400; }
        }
    """,
    js="""
        export default function({data, parentElement, setTriggerValue}) {
            const body = parentElement.querySelector("tbody");
            const fingerprint = JSON.stringify(data);
            if (body.dataset.fingerprint === fingerprint) return;
            body.dataset.fingerprint = fingerprint;
            const rows = data.map((option) => {
                const row = document.createElement("tr");
                const open = () => setTriggerValue("opened", option.key);
                row.onclick = (event) => {
                    if (!event.target.closest("button")) open();
                };
                const button = document.createElement("button");
                button.type = "button";
                button.textContent = option.listing;
                button.ariaLabel = "Review " + option.listing + ", " + option.variant;
                button.onclick = open;
                row.insertCell().append(button);
                row.insertCell().textContent = option.variant;
                const priority = document.createElement("span");
                priority.className = "priority " + option.colour;
                priority.textContent = option.priority;
                row.insertCell().append(priority);
                const confidence = row.insertCell();
                confidence.className = "score";
                confidence.textContent = option.confidence + "%";
                row.insertCell().textContent = option.verdict;
                return row;
            });
            body.replaceChildren(...rows);
        }
    """,
)
