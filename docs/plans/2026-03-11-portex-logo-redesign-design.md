# Portex Logo Redesign Design

## Goal

Redesign the README logo so it follows the composition and mascot energy of the reference `openclaw-logo-text-dark.png`, while replacing the lobster with a crab and replacing the wordmark with `PORTEX`.

## Reference

- Source image: `https://raw.githubusercontent.com/openclaw/openclaw/main/docs/assets/openclaw-logo-text-dark.png`

## Approved Direction

### Composition

- Use a horizontal lockup instead of the current standalone icon.
- Place the mascot on the left and the `PORTEX` wordmark on the right.
- Keep the background transparent so the asset renders cleanly on GitHub.

### Mascot

- Replace the lobster with a crab.
- Keep the overall reference mood: bold cartoon silhouette, strong contour, visible facial attitude, and exaggerated front claw.
- Do not reuse the current geometric front-facing crab as-is; redraw it in a more dynamic 3/4 view that reads closer to the reference.
- Preserve crab identity with a wider shell and no lobster tail segmentation.

### Color and Finish

- Keep the Portex palette direction: deep navy plus teal/cyan accents.
- Do not switch to the reference image's bright red primary color.
- Retain high contrast using a dark outer stroke and a light outline to keep the mascot readable at README scale.

### Wordmark

- Replace `openclaw` with `PORTEX`.
- Use all caps.
- Shape the letters as a chunky, slightly irregular, hand-drawn display wordmark closer to the reference than to a normal UI font treatment.
- Keep the wordmark visually integrated with the mascot rather than rendering plain text.

## README Integration

- Continue using a single shared SVG asset for both `README.md` and `README.zh-CN.md`.
- Keep the asset path stable at `assets/portex-crab-logo.svg` to minimize wiring changes.
- Update the README image width to suit the new horizontal logo.

## Delivery Boundary

This change includes:

- one redesigned SVG logo asset
- README wiring updates
- static contract test updates

This change does not include:

- PNG export
- favicon generation
- `web/` app icon integration
- alternate themes or logo variants

## Acceptance Criteria

- `assets/portex-crab-logo.svg` is redesigned as a horizontal mascot-plus-wordmark logo.
- The mascot reads as a crab with a style clearly inspired by the reference image.
- The wordmark reads `PORTEX` in all caps.
- `README.md` and `README.zh-CN.md` both render the shared asset near the top.
- Static tests lock the shared README reference and the new SVG contract.
