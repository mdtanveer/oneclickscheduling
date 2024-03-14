from projectclient import fetch_full_data
import processscheduler as ps
import jmespath
import json
from datetime import datetime

OPTIONS = {'friendly_names': True}

projclient = fetch_full_data()

pb_bs = ps.SchedulingProblem(name="1-click scheduling")#,
        #delta_time=timedelta(days=1),
        #start_time = datetime.now())

def add_working_days_to_date(start_date, days_to_add):
    from datetime import timedelta
    start_weekday = start_date.weekday()

    # first week
    total_days = start_weekday + days_to_add
    if total_days < 5:
        return start_date + timedelta(days=days_to_add)
    else:
        # first week
        total_days = 7 - start_weekday
        days_to_add -= 5 - start_weekday

        # middle whole weeks
        whole_weeks = days_to_add // 5
        remaining_days = days_to_add % 5
        total_days += whole_weeks * 7
        days_to_add -= whole_weeks * 5

        # last week
        total_days += remaining_days

        return start_date + timedelta(days=total_days)

class ExternalMapping:
    def __init__(self):
        self.tasks = {}
        self.resources = {}
        self.assignments = {}

MAP = ExternalMapping()

# resources
for resource in projclient.data["resources"]:
    resFriendlyName = resource["name"].rsplit(' ', 1)[0]
    r = ps.Worker(name=resFriendlyName if OPTIONS['friendly_names'] else resource['id'])
    MAP.resources[resource["id"]] = r

# tasks
for task in projclient.data["tasks"]:
    taskname = task['name'] if OPTIONS['friendly_names'] else task['id']
    t = ps.FixedDurationTask(name=taskname, duration=int(int(task['duration'])/28800))
    MAP.tasks[task['id']] = t
    #t.add_required_resource(ps.SelectWorkers(list_of_workers=MAP.resources.values(), nb_workers_to_select=1))

# dependencies
for link in projclient.data["links"]:
    predessorTask = MAP.tasks[link['predecessorId']]    
    successorTask = MAP.tasks[link['successorId']]    
    ps.TaskPrecedence(task_before=predessorTask, task_after=successorTask, kind='tight')

# assignments
for assignment in projclient.data["assignments"]:
    taskId = assignment['taskId']    
    resource = MAP.resources[assignment['resourceId']]    
    if taskId in MAP.assignments.keys():
        MAP.assignments[taskId].append(resource)
    else:
        MAP.assignments[taskId] = [resource]
for taskId in MAP.assignments.keys():
    task = MAP.tasks[taskId]
    if len(MAP.assignments[taskId]) > 1:
        task.add_required_resource(ps.SelectWorkers(list_of_workers=MAP.assignments[taskId], nb_workers_to_select=1))
    elif len(MAP.assignments[taskId]) == 1:
        task.add_required_resource(MAP.assignments[taskId][0])
    else:
        task.add_required_resource(ps.SelectWorkers(list_of_workers=MAP.resources.values(), nb_workers_to_select=1))

# add makespan objective
ps.ObjectiveMinimizeMakespan()

# plot solution
solver = ps.SchedulingSolver(problem=pb_bs)
solution = solver.solve()

if not OPTIONS["friendly_names"]:
    task_solution = json.loads(solution.to_json())

    assignments = jmespath.search('tasks.*.{taskId: name, resId: assigned_resources[0]}', task_solution)
    for assignment in assignments:
        #print(assignment["taskId"], assignment["resId"])
        resource = jmespath.search(f'[?id == `{assignment["resId"]}`]', projclient.data["resources"])[0]
        projclient.create_assignment(assignment["taskId"], resource)

    task_starts = jmespath.search('tasks.*.{taskId: name, start: start}', task_solution)
    for task_start in task_starts:
        project_start = datetime.now()
        start_offset = task_start["start"]
        start = add_working_days_to_date(project_start, start_offset) 
        print(task_start["taskId"], task_start["start"], start)

        # "2023-09-21T16:00:00.000Z"
        projclient.update_task(task_start["taskId"], {'start': start.strftime("%Y-%m-%dT16:00:00.000Z")})
else:
    print(solution.to_json())
    ps.render_gantt_matplotlib(solution)



