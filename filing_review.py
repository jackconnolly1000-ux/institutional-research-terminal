"""Display the EDGAR filing index without implying its documents were reviewed."""

import ui


def render(inventory: dict | None) -> str:
    if not inventory:
        return '<p class="irt-note">Not checked: this saved result has no subsequent-filing index.</p>'
    since, through = inventory["since"], inventory["through"]
    dates = f"from {ui.esc(since)} through {ui.esc(through)}" if since else "(balance-sheet date unavailable)"
    intro = (f"EDGAR submissions index {dates}. Forms listed: 8-K, 8-K/A, 424B series, FWP, S-3 series, "
             "10-K/A and 10-Q/A. Form and date alone do not establish a financing event. "
             "Document contents and exhibits: Not checked.")
    notes = "".join(f'<p class="irt-note">Not checked: {ui.esc(n)}</p>' for n in inventory["notes"])
    if inventory["status"] == "incomplete":
        notes = '<p class="irt-note">Filing index incomplete.</p>' + notes
    rows = []
    for f in inventory["filings"]:
        item = f" · {ui.eight_k_items(f['items'])}" if f["form"].startswith("8-K") and f["items"] else ""
        rows.append(f'<li><a href="{ui.esc(f["url"])}" target="_blank" rel="noopener noreferrer" '
                    f'style="color:var(--link)">{ui.esc(f["form"])} filed {ui.esc(f["filed"])} · '
                    f'{ui.esc(f["accession"])}</a>{ui.esc(item)} · Not checked</li>')
    empty = '<p class="irt-note">No candidate forms indexed for these dates; contents not reviewed.</p>'
    return (f'<p class="irt-note">{intro}</p>{notes}'
            + (f'<ol class="irt-ol" style="overflow-wrap:anywhere">{"".join(rows)}</ol>' if rows else empty))
