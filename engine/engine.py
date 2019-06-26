import functools
from .object import *
from .changes import *
from .schemas import WorldDumpSchema
from .commit_container import CommitContainer


class Cell(object):
    pass


class Task(object):
    """Suspended function.
    """

    foo = lambda: None

    def __init__(self, foo):
        self.foo = foo

    def run(self):
        self.foo()


class Engine(object):

    field = list()
    objects = dict()
    objects_counter = 0
    ais = dict()
    tasks_queue = list()

    def __init__(self, width=512, height=512):
        self.width = width
        self.height = height
        for _ in range(width):
            self.field.append([Cell() for _ in range(height)])

        self.commit_container = CommitContainer()

    def get_cell(self, x, y):
        if x < -self.width / 2 or x > self.width / 2 or y < -self.height / 2 or y > self.height / 2:
            raise ValueError("Coords value out of field range")

        return self.field[x + self.width // 2][y + self.height // 2]

    def add_object(self, obj, x, y):
        """ Complete object and append to other objects.

        :param obj: Already created object
        :return: Return object (or not???)
        """
        cell = self.get_cell(x, y)
        cell.object = obj
        obj.x, obj.y = x, y
        obj.id = self.objects_counter
        self.objects_counter += 1
        self.objects[obj.id] = obj
        self.commit_container.append_change(CreateChange(object=obj))

    def get_world_dump(self):
        """Returns touple of last commit id and world dumped to string.
        """
        last_commit_id = self.commit_container.get_last_commit_id()
        world = dict(
            last_commit_id = last_commit_id,
            width = self.width,
            height = self.height,
            objects = list(self.objects.values()))

        res, err = WorldDumpSchema().dump(world)
        return last_commit_id, res


    def suspend(f):
        """Decorator which adds given function to `tasks_queue` instead of perform it.
        All functions that calls from inside or from AI have to be decorated with this.
        """
        @functools.wraps(f)
        def wrapper(self, *args, **argv):
            task = Task(lambda: f(self, *args, **argv))
            self.tasks_queue.append(task)

        return wrapper

    @suspend
    def create_player(self, uid):
        """Debug method to create player.
        """
        p = Player(uid)
        self.add_object(p, 0, 0)

    def iterate_world(self):
        print(f"Iteration: task queue size: {len(self.tasks_queue)}")
        for t in self.tasks_queue:
            t.run()

        self.tasks_queue = [] 
        self.commit_container.push()
