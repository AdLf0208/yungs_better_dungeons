//! `betterdungeons` — YUNG's Better Dungeons for Horizon, slice 1: the small dungeon.
//!
//! | Moment | What the port does |
//! |---|---|
//! | [`Mod::register`] | registers the structure type `betterdungeons:small_dungeon_type` and requests the blocks its templates name |
//! | [`Mod::register_commands`] | declares `/betterdungeons status` |
//! | [`Mod::run_mod_command`] | answers it from [`runtime`] |
//!
//! The structure's own code lives on the registered type: [`support::SmallDungeonType`]
//! assembles the jar's carried jigsaw templates through [`runtime::assemble`], and
//! [`support::SmallDungeonPiece`] places one piece into the chunk the engine asks
//! about. Every number is in [`runtime`], which has no `mod_api` type and is
//! proved by `cargo test`; [`support`] is the thin glue.
//!
//! The carried tables ([`pools`], [`templates`]) are generated from the jar by
//! `tools/gen_tables.py`.
pub mod pools;
pub mod runtime;
pub mod support;
pub mod templates;

use mod_api::{
    self, Flow, Hooks, RegisterCommandsEvent, Registrar, RegistrationContext, RunModCommandEvent,
    ServerHost,
};

#[derive(Default)]
struct Mod;

#[mod_api::horizon_mod]
impl Hooks for Mod {
    /// Once, at startup: the structure type and the blocks it places.
    fn register(&self, r: &mut dyn Registrar, cx: &RegistrationContext) {
        support::register(r, cx);
    }

    /// Declare `/betterdungeons …` in the server's command tree.
    fn register_commands(&self, _host: &mut dyn ServerHost, event: &mut RegisterCommandsEvent<'_>) {
        support::declare_commands(event.commands);
    }

    /// Answer `/betterdungeons …` and take the command.
    fn run_mod_command(
        &self,
        host: &mut dyn ServerHost,
        event: &mut RunModCommandEvent<'_>,
    ) -> Flow {
        support::run_command(host, event)
    }
}
