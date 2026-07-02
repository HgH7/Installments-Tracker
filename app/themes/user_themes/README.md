# Creating Custom Themes

Theme files are JSON documents stored in `data/themes/`. Each JSON file must contain the following structure:

## Minimal theme

```json
{
  "name": "my-custom-theme",
  "is_dark": true,
  "colors": {
    "background": "#1a1a2e",
    "surface": "#16213e",
    "surface_high": "#1e2a45",
    "surface_low": "#0f0f23",
    "primary": "#2563eb",
    "text": "#ffffff",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",
    "border": "#2d3748",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6"
  }
}
```

## Full theme (with fonts and corner radius)

```json
{
  "name": "my-full-theme",
  "is_dark": false,
  "colors": {
    "background": "#f8fafc",
    "surface": "#ffffff",
    "surface_high": "#f1f5f9",
    "surface_low": "#e2e8f0",
    "primary": "#2563eb",
    "text": "#0f172a",
    "text_secondary": "#475569",
    "text_muted": "#94a3b8",
    "border": "#cbd5e1",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "info": "#3b82f6"
  },
  "fonts": {
    "heading": {"family": "Segoe UI", "size": 20, "weight": "bold"},
    "subheading": {"family": "Segoe UI", "size": 15, "weight": "bold"},
    "section": {"family": "Segoe UI", "size": 14, "weight": "bold"},
    "body": {"family": "Segoe UI", "size": 13, "weight": "normal"},
    "body_bold": {"family": "Segoe UI", "size": 13, "weight": "bold"},
    "small": {"family": "Segoe UI", "size": 11, "weight": "normal"},
    "label": {"family": "Segoe UI", "size": 11, "weight": "bold"},
    "data": {"family": "Courier New", "size": 12, "weight": "normal"},
    "button": {"family": "Segoe UI", "size": 13, "weight": "bold"}
  },
  "corner_radius": 8
}
```

## Color key reference

| Key              | Purpose                           |
|------------------|-----------------------------------|
| `background`     | Main window / page background     |
| `surface`        | Card / panel surface              |
| `surface_high`   | Elevated surface (hovered items)  |
| `surface_low`    | Depressed surface                 |
| `primary`        | Primary accent / action color     |
| `text`           | Primary text color                |
| `text_secondary` | Secondary / subdued text          |
| `text_muted`     | Muted / disabled text             |
| `border`         | Borders and dividers              |
| `success`        | Success / positive indicator      |
| `warning`        | Warning / caution indicator       |
| `danger`         | Error / destructive indicator     |
| `info`           | Informational indicator           |

## Font key reference

| Key          | Usage                        |
|--------------|------------------------------|
| `heading`    | Page / section titles        |
| `subheading` | Sub-section titles           |
| `section`    | Section headers (smaller)    |
| `body`       | Default body text            |
| `body_bold`  | Emphasised body text         |
| `small`      | Small / caption text         |
| `label`      | Form labels / badges         |
| `data`       | Monospaced data display      |
| `button`     | Button labels                |

## Applying a custom theme

Once the JSON file is placed in `data/themes/`, the theme will be available
on the next application start. You can also switch to it programmatically:

```python
from app.themes import theme_engine
theme_engine.apply("my-custom-theme")
```

## Using the event system

When a theme is applied, the theme engine emits a `app.theme_changed` event.
Subscribe to it to refresh UI elements:

```python
from app.events import dispatcher

def on_theme_changed(event):
    theme_name = event.data["theme"]
    theme = event.data["theme_obj"]
    # refresh your widgets here

dispatcher.on("app.theme_changed", on_theme_changed)
```
