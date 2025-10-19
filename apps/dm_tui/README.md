# **DM TUI — The Black Circuit Framework for Baator**

> “Where code and command converge, the Dungeon Master reigns.”

**DM TUI** is an interactive terminal framework built with [Textual](https://textual.textualize.io/).
It blends command-driven control, modular UI components, and extensible logic — a forge for storytellers, system operators, and digital magi who crave immediacy and elegance in their tools.

---

## ⚙️ Features

- **Command Router Core** – Self-wiring registry for command classes. Drop in new modules; they register automatically.
- **Dynamic Help System** – Real-time introspection of all available commands.
- **Autoscrolling Log & Graceful Exit** – No curses residue, no manual paging.
- **Minimal Dependencies** – Just Textual and Rich. Lightweight yet powerful.
- **Extensible Architecture** – Each command lives as its own class, wired through the router.

---

## 🧰 Installation

```bash
git clone https://github.com/aetheric-forge/BlackCircuit-dm_tui.git
cd BlackCircuit-dm_tui
pip install -e .
```

Requires **Python ≥ 3.11**

---

## 💻 Usage

```bash
dm-tui
```

Inside the console:
```
help      # lists available commands
quit      # exits cleanly
```

Create new commands under `dm_tui/commands/` by subclassing `BaseCommand` and implementing `execute()`.

---

## 🧩 Project Structure

```
dm_tui/
 ├── app/              # Core router and app logic
 ├── commands/         # Command modules (help, quit, etc.)
 ├── ui/               # Textual UI components
 └── ...
dm_tui.py              # Console entrypoint
pyproject.toml
requirements.txt
```

---

## 🕯️ Philosophy

The Black Circuit is more than a CLI — it’s a ritual interface, a liminal zone where user intent, system state, and narrative logic entwine.
Every command is invocation and computation; every log line, a whisper from the machine.

**Baatorian Principle:** *“Form is function, but function must evoke awe.”*

---

## 📜 License

**Aetheric General License v1.0 (AGL)**
A permissive-gothic license for creative and technical works of the Forge.

---

## 🧠 Roadmap

- Session persistence & replay
- Command-context stack (nested modes)
- Dynamic window layouts
- Integration with Aetheric Forge services
