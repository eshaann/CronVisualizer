from croniter import croniter
from datetime import datetime, timedelta

def expand_cron(cron_expr, days=7):
    now = datetime.utcnow()
    end = now + timedelta(days=days)

    itr = croniter(cron_expr, now)
    times = []

    next_time = itr.get_next(datetime)

    while next_time <= end:
        times.append(next_time)
        next_time = itr.get_next(datetime)

    return times

def build_run_map(workflows):
    run_map = {}

    for wf in workflows:
        run_map[wf["name"]] = []

        for cron in wf["cron"]:
            run_map[wf["name"]].extend(expand_cron(cron))

    return run_map

def propagate_dependencies(workflows, run_map):
    name_to_wf = {wf["name"]: wf for wf in workflows}

    changed = True

    while changed:
        changed = False

        for wf in workflows:
            if wf["depends_on"]:
                all_times = set(run_map.get(wf["name"], []))  # current times

                for parent in wf["depends_on"]:
                    parent_times = run_map.get(parent, [])
                    all_times.update(parent_times)  # add parent times

                new_times = sorted(all_times)

                if new_times != run_map.get(wf["name"], []):
                    run_map[wf["name"]] = new_times
                    changed = True

    return run_map

def build_events(run_map):
    events = []

    for wf_name, times in run_map.items():
        for t in times:
            events.append({
                "workflow": wf_name,
                "time": t
            })

    return sorted(events, key=lambda x: x["time"])