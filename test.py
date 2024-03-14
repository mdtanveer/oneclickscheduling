import processscheduler as ps
from datetime import timedelta, datetime

pb_bs = ps.SchedulingProblem("1-click scheduling")#,
        #delta_time=timedelta(days=1),
        #start_time = datetime.now())

# tasks
t1 = ps.FixedDurationTask('t1', duration=4)
t2 = ps.FixedDurationTask('t2', duration=5)
t3 = ps.FixedDurationTask('t3', duration=6)
t4 = ps.FixedDurationTask('t4', duration=3)
t5 = ps.FixedDurationTask('t5', duration=4)
t6 = ps.FixedDurationTask('t6', duration=1)
t7 = ps.FixedDurationTask('t7', duration=3)
t8 = ps.FixedDurationTask('t8', duration=2)
t9 = ps.FixedDurationTask('t9', duration=5)
t10 = ps.FixedDurationTask('t10', duration=2)
t11 = ps.FixedDurationTask('t11', duration=3)
t12 = ps.FixedDurationTask('t12', duration=6)

# workers
Megha = ps.Worker('Megha')
Tanveer = ps.Worker('Tanveer')
Spandana = ps.Worker('Spandana')

RESOURCES = [Megha, Tanveer, Spandana]

# precedence constraints
ps.TaskPrecedence(t1, t2, kind='tight')
ps.TaskPrecedence(t3, t4, kind='tight')
ps.TaskPrecedence(t5, t6, kind='tight')
ps.TaskPrecedence(t8, t9, kind='tight')

# resource assignment
t1.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t2.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t3.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t4.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t5.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t6.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t7.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t8.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t9.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t10.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t11.add_required_resource(ps.SelectWorkers(RESOURCES, 1))
t12.add_required_resource(ps.SelectWorkers(RESOURCES, 1))

# add makespan objective
pb_bs.add_objective_makespan()

# plot solution

#ps.ResourceUnavailable(Spandana, [(3,6)])
solver = ps.SchedulingSolver(pb_bs)
solution = solver.solve()
solution.render_gantt_matplotlib()
print(solution.to_json_string())
