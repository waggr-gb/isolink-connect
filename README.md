# Isolink Connect SDKs

Isolink Connect lets a local application request access to its own spaces and records in the Isolink desktop app.

## KScript

Install the SDK into a KScript project using a build with manifest-based library installation and `KScript.Net`'s `@with_loopback_json` command.

```sh
kscript repo add waggr-gb/isolink-connect
kscript lib add waggr-gb/isolink-connect@isolink-connect
```

The repository project manifest configures the tests and points to the SDK folder. On KScript builds that support this reference, a direct install with `kscript lib add waggr-gb/isolink-connect` installs the same folder as the named command above. The SDK's version, entry point and runtime packages are declared in its own manifest. [Repository project manifest](kscript.json) · [SDK manifest](libraries/isolink-connect/kscript.json)

The [KScript SDK guide](libraries/isolink-connect/README.md) covers sessions, space and record operations, field edits, and upgrading the import. The [source client](libraries/isolink-connect/client.kscript) runs the [Connect v1 protocol](libraries/isolink-connect/src/protocol.kscript) over the scoped JSON transport in `KScript.Net`.

From a checkout, run the protocol tests with `kscript test tests`. They use a scripted peer and run without the Isolink desktop app. With Isolink open and a KScript build that supports `@with_loopback_json`, run the [notes example](examples/notes.kscript):

```sh
kscript examples/notes.kscript
```

The example asks for consent, opens the app's notes space and writes a sample shopping note.
