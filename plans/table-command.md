# Table Command Plan

## Feature
Command `table one`...`table nine` moves cursor to predefined 3x3 grid zones.

## Grid Layout
```
7 8 9
4 5 6
1 2 3
```

## Zone Coordinates (center of each zone)
| Zone | x (fraction) | y (fraction) |
|------|--------------|--------------|
| 1 | 1/6 | 5/6 |
| 2 | 3/6 | 5/6 |
| 3 | 5/6 | 5/6 |
| 4 | 1/6 | 3/6 |
| 5 | 3/6 | 3/6 |
| 6 | 5/6 | 3/6 |
| 7 | 1/6 | 1/6 |
| 8 | 3/6 | 1/6 |
| 9 | 5/6 | 1/6 |

## Implementation Formula
```
row = (number - 1) % 3      # 0, 1, 2
col = 2 - (number - 1) // 3  # 2, 1, 0

xpoint = (2 * row + 1) * x / 6
ypoint = (2 * col + 1) * y / 6
```

## Changes Required

### 1. parsepackage/command_parser.py

#### Add to `__init__`:
```python
self.table_zones = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
```

#### Add to `commandlist`:
Add `self.table_zones` to the commandlist tuple.

#### Add to `commands` list:
Add `"table"` to the commands list.

#### Add to `evaluate_command`:
```python
elif command_buffer[0] == "table":
    if len(command_buffer) >= 2:
        if command_buffer[1] in self.table_zones:
            number = int(self.word_to_int(command_buffer[1]))
            row = (number - 1) % 3  # 0, 1, 2
            col = 2 - (number - 1) // 3  # 2, 1, 0
            x, y = screenSize()
            xpoint = (2 * row + 1) * x / 6
            ypoint = (2 * col + 1) * y / 6
            moveMouseAbs(xpoint, ypoint)
            command_buffer = ["table"]
        else:
            return self.handle_invalid_command(
                command_buffer[1], command_buffer
            )
```

### 2. docs/userguide.md

Add to command reference:
```
- `table [one-nine]` - move mouse to zone on 3x3 grid (7 top-left, 5 center, 1 bottom-left)
```

## Usage Examples
- `table one` - moves to bottom-left zone
- `table five` - moves to center
- `table nine` - moves to top-right zone
