import processscheduler as ps
from datetime import timedelta, datetime

pb_bs = ps.SchedulingProblem(name="1-click scheduling")#,
        #delta_time=timedelta(days=1),
        #start_time = datetime.now())

# tasks
t1 = ps.FixedDurationTask(name='t1', duration=4)
t2 = ps.FixedDurationTask(name='t2', duration=5)
t3 = ps.FixedDurationTask(name='t3', duration=6)
t4 = ps.FixedDurationTask(name='t4', duration=3)
t5 = ps.FixedDurationTask(name='t5', duration=4)
t6 = ps.FixedDurationTask(name='t6', duration=1)
t7 = ps.FixedDurationTask(name='t7', duration=3)
t8 = ps.FixedDurationTask(name='t8', duration=2)
t9 = ps.FixedDurationTask(name='t9', duration=5)
t10 = ps.FixedDurationTask(name='t10', duration=2)
t11 = ps.FixedDurationTask(name='t11', duration=3)
t12 = ps.FixedDurationTask(name='t12', duration=6)

# workers
Megha = ps.Worker(name='Megha')
Tanveer = ps.Worker(name='Tanveer')
Spandana = ps.Worker(name='Spandana')

RESOURCES = [Megha, Tanveer, Spandana]

# precedence constraints
ps.TaskPrecedence(task_before=t1, task_after=t2, kind='tight')
ps.TaskPrecedence(task_before=t3, task_after=t4, kind='tight')
ps.TaskPrecedence(task_before=t5, task_after=t6, kind='tight')
ps.TaskPrecedence(task_before=t8, task_after=t9, kind='tight')

# resource assignment
t1.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=2))
t2.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t3.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t4.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t5.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t6.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t7.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t8.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t9.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t10.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t11.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))
t12.add_required_resource(ps.SelectWorkers(list_of_workers=RESOURCES, nb_workers_to_select=1))

# add makespan objective
ps.ObjectiveMinimizeMakespan()

# plot solution

#ps.ResourceUnavailable(Spandana, [(3,6)])
solver = ps.SchedulingSolver(problem=pb_bs)

for r in RESOURCES:
    res_utilization = ps.IndicatorResourceUtilization(resource=r)
solution = solver.solve()
ps.render_gantt_matplotlib(solution)
print(solution.to_json())
print(solution.indicators)
