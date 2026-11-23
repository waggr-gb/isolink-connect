"""Exercise the installed SDK against an independent Connect v1 TCP peer."""

import argparse
import json
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path


SET = {"op": "setValue", "field": 1, "value": "hello"}
EDITS = [
    {"op": "addToCounter", "field": 2, "by": 3},
    {"op": "addToSet", "field": 3, "items": ["done"]},
    {"op": "removeFromSet", "field": 3, "items": ["draft"]},
]
SPACE = {"id": "space1", "name": "Home", "key": "home", "people": [], "admin": True}
RECORD = {"id": "one", "type": "note", "fields": {"2": 3, "3": ["done"]}}
APP = {"id": "example.kscript", "name": "Test App"}
DEADLINE = 15


def verify_server(stream, scenario):
    """Validate every outgoing method, ID, and parameter, then send the host reply."""
    sequence = 0

    def exchange(method, params, result):
        nonlocal sequence
        sequence += 1
        line = stream.readline()
        expected = {"id": sequence, "m": method, "p": params}
        # JSON distinguishes booleans from integers (Python normally treats True and 1 as equal).
        if not line or json.dumps(json.loads(line), sort_keys=True) != json.dumps(expected, sort_keys=True):
            raise AssertionError(f"Expected {expected!r}, received {line!r}")
        stream.write(json.dumps({"id": sequence, "r": result}).encode() + b"\n")

    hello = {"protocol": 1, "app": APP}
    if scenario != "callback error":
        hello["token"] = "saved"
    host = {
        "protocol": 1, "mode": "host", "capabilities": [],
        "me": {"handle": "h_00000000000000000000000000000001", "name": "Joan", "me": True},
    }
    if scenario != "records":
        host["token"] = "renewed"
    exchange("hello", hello, host)

    if scenario == "records":
        exchange("spaces.list", {}, [SPACE])
        exchange("spaces.get", {"space": "space1"}, SPACE)
        exchange("records.list", {"space": "space1"}, [RECORD])
        exchange("records.list", {"space": "space1", "type": "task"}, [])
        exchange("records.get", {"space": "space1", "id": "missing"}, None)
        exchange("records.edit", {"space": "space1", "type": "note", "id": "one", "edits": EDITS}, RECORD)
        exchange("records.delete", {"space": "space1", "id": "one"}, None)
    else:
        exchange("status", {}, {"running": True, "reachable": True})
        exchange("spaces.open", {"key": "home", "name": "Home"}, SPACE)
        exchange("records.edit", {"space": "space1", "type": "note", "id": "one", "edits": [SET]},
                 {"id": "one", "type": "note", "fields": {"1": "hello"}})
    if stream.readline() != b"":
        raise AssertionError("Expected the SDK to close the connection when the callback ended")


def program(entry, port, scenario):
    if scenario == "records":
        body = """
          echo $session.token
          spaces = @link.list_spaces($session)
          space = @link.get_space($session, $spaces[0].id)
          echo $space.name
          all = @link.list_records($session, $space.id)
          echo $all->count()
          tasks = @link.list_records($session, $space.id, type: 'task')
          echo $tasks->count()
          missing = @link.get_record($session, $space.id, 'missing')
          echo $missing == null
          edits = [@link.add_to_counter(2, 3), @link.add_to_set(3, ['done']), @link.remove_from_set(3, ['draft'])]
          note = @link.edit_record($session, $space.id, 'note', 'one', $edits)
          echo $note.fields['2']
          removed = @link.delete_record($session, $space.id, $note.id)
          return $removed == null"""
    else:
        body = """
          status = @link.status($session)
          echo $status.running
          echo $session.token
          space = @link.open_space($session, 'home', 'Home')
          note = @link.edit_record($session, $space.id, 'note', 'one', [@link.set_value(1, 'hello')])
          """
        body += 'throw Validation "callback failed"' if scenario == "callback error" else "return $note.fields['1']"
    token = "" if scenario == "callback error" else ", token: 'saved'"
    return (f'import "lib/isolink-connect/{entry}" as link\nfn run(session) {{\n{body}\n}}\n'
            f"echo @link.with_session('example.kscript', 'Test App', @run{token}, port: {port})\n")


def test_session(cli, project, entry, scenario, expected):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        server.settimeout(DEADLINE)
        caller = project / "wire-client.kscript"
        caller.write_text(program(entry, server.getsockname()[1], scenario), encoding="utf-8")
        with subprocess.Popen([*cli, str(caller)], cwd=project, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as client:
            try:
                connection, _ = server.accept()
                with connection:
                    connection.settimeout(DEADLINE)
                    with connection.makefile("rwb", buffering=0) as stream:
                        verify_server(stream, scenario)
                output, error = client.communicate(timeout=DEADLINE)
            except Exception as cause:
                client.kill()
                output, error = client.communicate()
                raise AssertionError(f"{scenario}: {cause}\nKScript output:\n{output}{error}") from cause
        failed = scenario == "callback error"
        if output != expected or (client.returncode != 0) != failed or (failed and "callback failed" not in error):
            raise AssertionError(f"{scenario}: KScript exited {client.returncode}: stdout={output!r}, stderr={error!r}")
    print(f"PASS {scenario}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kscript", default="kscript", help="KScript executable or KScript.dll")
    parser.add_argument("--library", type=Path, default=Path(__file__).resolve().parents[1] / "libraries/isolink-connect",
                        help="SDK package folder, including its kscript.json manifest")
    args = parser.parse_args()
    cli = ["dotnet", str(Path(args.kscript).resolve())] if args.kscript.endswith(".dll") else [shutil.which(args.kscript) or args.kscript]
    with tempfile.TemporaryDirectory(prefix="isolink-wire-") as temp:
        project = Path(temp)
        sdk = project / "lib/isolink-connect"
        shutil.copytree(args.library, sdk)
        entry = json.loads((sdk / "kscript.json").read_text(encoding="utf-8"))["library"]["entry"]
        test_session(cli, project, entry, "session", "true\nrenewed\nhello\n")
        test_session(cli, project, entry, "callback error", "true\nrenewed\n")
        test_session(cli, project, entry, "records", "saved\nHome\n1\n0\ntrue\n3\ntrue\n")


if __name__ == "__main__":
    main()
