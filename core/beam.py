from core.loads import Load, PointLoad, ReactionForce
from core.types import BeamType, LoadFunction


class Beam:
    def __init__(self, beam_type: BeamType, beam_length: float):
        self.type: BeamType = beam_type
        self.continuous_loads: list[Load] = []
        self.point_loads: list[PointLoad] = []
        self.total_load: float = 0
        self.reaction_left = ReactionForce(0, 0)
        self.reaction_right = ReactionForce(0, beam_length)

    def get_second_moment_of_area(self) -> float:
        pass

    def get_first_moment_of_area(self, y) -> float:
        pass

    def set_load_function(self, start: float, end: float, function: LoadFunction):
        self.continuous_loads.append(Load(start, end, function))

    def set_point_load(self, load, x):
        self.point_loads.append(PointLoad(magnitude=load, position=x))

    def update_loads(self):
        sum_moments = 0
        sum_load = 0
        for load in self.continuous_loads:
            average_load = load.get_area()
            sum_load += average_load
            sum_moments += average_load * load.get_avg_value_point()
        for load in self.point_loads:
            sum_load += load.magnitude
            sum_moments += load.magnitude * load.position

        self.reaction_left.magnitude = (sum_moments - self.reaction_right.position * sum_load) / (
                self.reaction_left.position - self.reaction_right.position)
        self.reaction_right.magnitude = sum_load - self.reaction_left.magnitude
        self.total_load = sum_load

    def get_shear_force(self, x: float):
        sum_left = 0
        for load in self.continuous_loads:
            if load.start > x:  # skip right side loads
                continue
            sum_left += load.get_area(0, x)
            pass
        for load in self.point_loads:
            if load.position > x:  # skip right side loads
                continue
            sum_left += load.magnitude
        if x < self.reaction_right.position:
            return self.reaction_left.magnitude - sum_left
        else:
            return self.reaction_left.magnitude + self.reaction_right.magnitude - sum_left

    def get_bending_moment(self, x: float):
        sum_moments = 0
        for load in self.continuous_loads:
            if load.start > x:  # skip right side loads
                continue
            avg_load_pos_x = load.get_avg_value_point(0, x)
            avg_load = load.get_area(0, x)
            sum_moments += (x - avg_load_pos_x) * avg_load
        for load in self.point_loads:
            if load.position > x:  # skip right side loads
                continue
            sum_moments += (x - load.position) * load.magnitude
        reaction_moment_left = self.reaction_left.magnitude * (x - self.reaction_left.position)
        if x < self.reaction_right.position:
            return reaction_moment_left - sum_moments
        else:
            reaction_moment_right = self.reaction_right.magnitude * (x - self.reaction_right.position)
            return reaction_moment_left + reaction_moment_right - sum_moments

    def get_width(self, y: float) -> float:
        pass

    def get_height(self) -> float:
        pass
