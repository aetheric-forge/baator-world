# Baator World Roadmap

## Vision

Baator World is a multi-purpose game world which can be used for anything ranging from
simple combat resolution, to multi-session living campaigns. It is built in a modular
fashion to allow development of new rulesets and lore databases, as well as customizable
AI DM. Baator itself encompasses both the simulator and rules engines, but it also consists
of a lore database and high-level storyboarding assistance, as well as the ability to
repeatedly simulate scenes as insipiration.

Baator World comprises two interlinked systems: the Baatorian Simulator (mechanical resolution and rules logic) and the Novel Scene Simulator (narrative synthesis and lore contextualization). Together, they enable both tactical play and emergent storytelling.

## Principles

1. Baator is a unique world, but it is not the only world. It is opinionated only inasmuch as its system is based on well-known d20 mechanics. But there is absolutely no reason another could not use the same engine for a completely different probabilistic interpretation.
2. We do not judge how a creator or worldbuilder chooses to resolve its probability. While every effort has been made to provide a fair die, it is certainly not imperative that this be so, though this implementation is left as an exercise for the reader.
3. Baator serves as an example for others to design their own game worlds. While the Baatorian Lore is covered by the [licence](LICENSE.md), community development and remixing is to be encouraged, as well as providing tools for collaboration between creators.
4. Determinism and reproducibility are core to trust in simulation. Any scene generated under a given seed should be exactly reproducible, ensuring fair comparison between iterations or replays.

## Tech Stack

1. **GNU/Linux**
2. **Python** - expressive and introspective, the glue for simulation logic and YAML parsing
3. **RabbitMQ** - message bus enabling modular simulation and streaming narration
4. **Vue.js/Typescript**
5. **MongoDB** - ideal for flexible lore documents and event logs
6. **WSS (WebSocket Server)** - provides real-time observability for both game state and generated prose.

SSO has been dropped for an open world implementation, though the reader is certainly welcome to create private worlds by implementing their own SSO.

## Roadmap

1. Simulator, dice, and rules engine (v0.4.0) - Completed 2025-10-25
2. Archetypes & encounter presets (v0.5.0)
   * Striker/Defender/Adept base classes
   * YAML encounter schema
3. GenAI narrative layer (v0.6.0)
   * JSONL -> Markdown prose transformer, lore context injection
4. LoreDB integration (v0.7.0)
   * MongoDB lore API
   * scene tagging for world continuity
5. Persistent world campaigns (v1.0.0)

