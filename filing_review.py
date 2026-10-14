"""Display the EDGAR filing index and accession-specific, source-checked findings."""

import ui


def render(inventory: dict | None) -> str:
    if not inventory:
        return '<p class="irt-note">Not checked: this saved result has no subsequent-filing index.</p>'
    since, through = inventory["since"], inventory["through"]
    dates = f"from {ui.esc(since)} through {ui.esc(through)}" if since else "(balance-sheet date unavailable)"
    checked = sum(f.get("review", "").startswith("Checked ") for f in inventory["filings"])
    unreviewed = len(inventory["filings"]) - checked
    checked_through = max((f["review"].removeprefix("Checked ") for f in inventory["filings"]
                           if f.get("review", "").startswith("Checked ")), default="")
    intro = (f"EDGAR submissions index {dates}. Forms listed: 8-K, 8-K/A, 424B series, FWP, S-3 series, "
             "10-K/A and 10-Q/A. Form and date alone do not establish a financing event. ")
    if checked:
        intro += f"{checked} indexed document(s) manually checked as of {ui.esc(checked_through)}. "
        if unreviewed:
            intro += f"{unreviewed} indexed document(s) Not checked; review coverage is incomplete. "
        elif inventory["status"] == "incomplete" or through > checked_through:
            intro += "The index or review dates do not establish complete coverage. "
        else:
            intro += "All indexed candidates for these dates were checked. "
        intro += "Later events are not added to the dated balance-sheet debt or cash figures."
    else:
        intro += "Document contents and exhibits: Not checked."
    notes = "".join(f'<p class="irt-note">Not checked: {ui.esc(n)}</p>' for n in inventory["notes"])
    if inventory["status"] == "incomplete":
        notes = '<p class="irt-note">Filing index incomplete.</p>' + notes
    rows = []
    for f in inventory["filings"]:
        item = f" · {ui.eight_k_items(f['items'])}" if f["form"].startswith("8-K") and f["items"] else ""
        label = (f'<a href="{ui.esc(f["url"])}" target="_blank" rel="noopener noreferrer" '
                 f'style="color:var(--link)">{ui.esc(f["form"])} filed {ui.esc(f["filed"])} · '
                 f'{ui.esc(f["accession"])}</a>{ui.esc(item)}')
        if f.get("review", "").startswith("Checked ") and f.get("source_url"):
            related = "".join(
                f' · <a href="{ui.esc(url)}" target="_blank" rel="noopener noreferrer">{ui.esc(name)}</a>'
                for name, url in f.get("related", []))
            event = f" · Event {ui.esc(f['event_date'])}" if f.get("event_date") else ""
            rows.append(f'<li>{label} · {ui.esc(f["review"])}{event}<br>'
                        f'<strong>{ui.esc(f["kind"])}</strong>: {ui.esc(f["finding"])}<br>'
                        f'<a href="{ui.esc(f["source_url"])}" target="_blank" rel="noopener noreferrer">'
                        f'Source document</a>{related}</li>')
        else:
            rows.append(f'<li>{label} · Not checked</li>')
    empty = '<p class="irt-note">No candidate forms indexed for these dates; contents not reviewed.</p>'
    return (f'<p class="irt-note">{intro}</p>{notes}'
            + (f'<ol class="irt-ol" style="overflow-wrap:anywhere">{"".join(rows)}</ol>' if rows else empty))
