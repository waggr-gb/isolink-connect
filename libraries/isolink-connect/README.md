# Isolink Connect for KScript

Use this library from a KScript program on the same Windows, macOS or Linux computer as Isolink. It opens the Isolink desktop consent window on first use and gives the program access to its own spaces and records.

```sh
kscript repo add waggr-gb/isolink-connect
kscript lib add waggr-gb/isolink-connect@isolink-connect
```

The [package manifest](kscript.json) declares SDK version 0.3.0 and its entry. Use a KScript build with manifest-based installation and the generic `@with_loopback_json` command in `KScript.Net`. The SDK implements the Connect v1 handshake and request protocol in KScript. When upgrading an application that imports `lib/isolink-connect/index.kscript`, switch that import to `lib/isolink-connect/client.kscript` and keep the alias used by your application.

From a script next to the project's `lib` folder, pass a function to `with_session`. Use a stable app id so later runs can reopen the same space.

```kscript
import "lib/isolink-connect/client.kscript" as isolink

fn host_status() =>
  @isolink.with_session('com.example.notes', 'My Notes', fn(session) => @isolink.status($session))
```

`@host_status()` returns a map with the host's `running` flag. Catch connection failures where your app can report them. `with_session` returns the callback's result and closes the connection when the callback finishes, including when it throws. During the callback, `$session.me` identifies the current person. If Isolink issues a reconnect token, store `$session.token` in your app's private storage and pass it as `token:` on the next call. Isolink controls consent and revocation.

| Function | Result |
| --- | --- |
| `status(session)` | Host status with `running` and `reachable` flags |
| `list_spaces(session)`, `get_space(session, space)` | The app's spaces or one space by id |
| `open_space(session, key, name)` | The space for this stable key, created on first use |
| `list_records(session, space, type?)` | Records in the space, optionally filtered by type |
| `get_record(session, space, id)` | The record or `null` |
| `edit_record(session, space, type, id, edits)` | The created or updated record |
| `delete_record(session, space, id)` | Deletes the record and returns `null` |

Edits use integer field ids from 1 to 65535. Build them with `set_value(field, value)`, `add_to_counter(field, by)`, `add_to_set(field, items)` or `remove_from_set(field, items)`. Counter increments are positive integers. Sets take a list of items.

The library uses the desktop Connect v1 protocol on loopback and requests the standard app data grant. The wire format and consent model are described in the [Isolink Connect documentation](https://isolink.app/docs/connect.html#protocol).


## Protocol behavior

The source client opens the desktop endpoint on loopback port 47231, sends a v1 `hello` request with the app identity, and checks the host mode, protocol version and identity. It uses a renewed token when the host supplies one. Pass `port:` to `with_session` to connect to an Isolink host on another local port.

Each operation has a request ID and waits for its matching reply. Unrelated events are ignored while waiting. A `closed` event raises a `Network` error with code `not_connected`. A refusal from the host preserves its error code on `$err.code`. A refused operation can be caught inside the callback so the next operation can use the same connection. Malformed or mismatched replies invalidate the connection.
