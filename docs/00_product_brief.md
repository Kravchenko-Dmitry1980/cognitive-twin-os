# Product Brief

## Vision

**Cognitive Twin OS** is a cognitive/operational digital twin for decision support, memory continuity, evidence-based recommendations, and controlled learning.

It models a person's or organization's operational knowledge as structured, governable memory — not as an opaque LLM context window.

## Problem

Modern AI assistants optimize for conversational fluency, not durable cognition:

- Memory is fragmented across chats, files, and ad-hoc RAG indexes
- Provenance and consent are afterthoughts
- Recommendations lack traceable evidence
- Learning from outcomes is uncontrolled or absent

## Solution

An event-driven memory platform where:

1. **Events** capture atomic observations with source, actor, provenance, and governance
2. **Episodes** group events into meaningful memory units with salience and lifecycle state
3. **Policies** enforce sensitivity, consent, and retention before memory is used or shared
4. **Retrieval** returns evidence-linked context for decisions
5. **Evaluation** measures recall quality and recommendation accuracy over time

## Target users (future)

- Knowledge workers needing decision support with audit trails
- Teams building personal/organizational digital twins
- Researchers studying memory-centric agent architectures

## Non-goals (Phase 0/1)

- Chat UI or voice interface
- Autonomous agent swarms
- Real-time LLM inference
- Persona mimicry without evidence grounding

## Success criteria (Phase 1)

- All contracts validate in CI
- Events and episodes can be stored and retrieved in-memory
- Documentation defines clear boundaries for each layer
- No runtime dependency on LLM providers or external services
