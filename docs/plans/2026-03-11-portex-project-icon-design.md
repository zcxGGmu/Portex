# Portex Project Icon Design

## Goal

Add a README-ready Portex project icon built around a cartoon crab with a technical, logo-like visual language instead of a playful mascot style.

## Constraints

- Deliver a single primary SVG asset only.
- Keep the change scoped to repository-facing documentation and static assets.
- Preserve the current README information architecture; add the icon without rewriting the document.
- Reuse the same icon in both `README.md` and `README.zh-CN.md`.

## Visual Direction

### Recommended Concept: Portal Crab

Use a front-facing crab icon with geometric symmetry and a restrained expression. The crab should remain recognizable as a cartoon character, but it should read primarily as a project mark.

### Shape Language

- Symmetric front view
- Rounded central shell
- Raised claws framing the body
- Minimal eyes or antenna-like stalks
- Subtle outer ring or enclosing contour to imply a portal / gateway

### Style Rules

- Flat vector illustration
- Transparent background
- Clean strokes and large readable shapes
- No exaggerated facial expression
- No mascot-style embellishments such as blush, tongue, or uneven doodle lines

### Color Rules

- Primary: deep navy
- Secondary: teal / cyan accent
- Avoid bright crab red, which would pull the icon toward a playful mascot aesthetic

## README Integration

- Store the asset at `assets/portex-crab-logo.svg`.
- Display the icon near the top of both README files.
- Keep the layout simple and GitHub-friendly: centered image block between the title and the project description.
- Use alt text that identifies it as the Portex project logo.

## Delivery Boundary

This design intentionally does not include:

- favicon generation
- PNG exports
- social preview cards
- `web/` app icon integration
- alternate color themes or icon variants

## Acceptance Criteria

- A new SVG logo asset exists in the repository.
- Both README files render the logo near the top using the shared asset.
- The icon reads as a stylized technical crab rather than a purely cute mascot.
- The README structure remains otherwise intact.
