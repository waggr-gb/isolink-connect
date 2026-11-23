# Isolink Connect SDKs

Isolink Connect lets a local application request access to its own spaces and records in the Isolink desktop app.

## KScript

Install the SDK into a KScript project using a build with manifest-based library installation and `KScript.Net`'s `@with_loopback_json` command.

```sh
kscript repo add waggr-gb/isolink-connect
kscript lib add waggr-gb/isolink-connect@isolink-connect
```

The [repository project manifest](kscript.json) declares SDK version 0.3.0 and its entry when working from a checkout. The [library manifest](libraries/isolink-connect/kscript.json) declares the entry relative to the installed folder.

The [KScript SDK guide](libraries/isolink-connect/README.md) covers sessions, space and record operations, field edits, and upgrading the import. The [source client](libraries/isolink-connect/client.kscript) runs the [Connect v1 protocol](libraries/isolink-connect/src/protocol.kscript) over the scoped JSON transport in `KScript.Net`.

From a checkout, run the scripted protocol suite with `kscript test tests`. Run `python3 tests/wire.py` to exercise the SDK against a real loopback TCP peer, including token renewal, record edits and connection closure after a callback error. Both suites run without the desktop app. The SDK's CI also installs the exact revision under test, restores it in a fresh consumer, and runs the wire tests against the restored package.

With Isolink open and a compatible KScript build, run the [notes example](examples/notes.kscript):

```sh
kscript examples/notes.kscript
```

The example asks for consent, opens the app's notes space and writes a sample shopping note.
