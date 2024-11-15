import re
import random
import matplotlib.pyplot as plt


class Lexer:
    def __init__(self, text):
        self.text = text
        self.tokens = []
        self.current_pos = 0

    def tokenize(self):
        patterns = [
            (r"\bПостав(ити|лено|те)\b", "PLACE"),
            (r"\bточк(у|а|ою|и)\b", "POINT"),
            (r"\b(Побуд(увати|уйте|ова))\b", "BUILD"),
            (r"\bпрямокутн(ик|ика|ику|иком|и)\b", "RECTANGLE"),
            (r"\bтрикутн(ик|ика|ику|иком|и)\b", "TRIANGLE"),
            (r"\bПров(ести|едено)\b", "CONNECT"),
            (r"\bвідріз(ок|ка|ку|ком|ки)\b", "LINE"),
            (r"[A-Z]", "ID"),
            (r"\(", "LPAREN"),
            (r"\)", "RPAREN"),
            (r",", "COMMA"),
            (r"-?\d+(\.\d+)?", "NUMBER"),
            (r"\.", "DOT"),
        ]

        for pattern, token_type in patterns:
            for match in re.finditer(pattern, self.text):
                self.tokens.append((token_type, match.group(), match.start()))

        self.tokens.sort(key=lambda x: x[2])

        return [(token_type, value) for token_type, value, _ in self.tokens]


class Node:
    pass


class PointNode(Node):
    def __init__(self, name, x, y):
        self.name = name
        self.x = float(x)
        self.y = float(y)

    def __repr__(self):
        return f"Point({self.name}, {self.x}, {self.y})"


class RectangleNode(Node):
    def __init__(self, points):
        self.points = points

    def __repr__(self):
        return f"Rectangle({self.points})"


class TriangleNode(Node):
    def __init__(self, points):
        self.points = points

    def __repr__(self):
        return f"Triangle({self.points})"


class LineNode(Node):
    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2

    def __repr__(self):
        return f"Line({self.point1}, {self.point2})"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.built_points = {}

    def consume(self, token_type):
        if self.pos < len(self.tokens) and self.tokens[self.pos][0] == token_type:
            value = self.tokens[self.pos][1]
            self.pos += 1
            return value
        raise SyntaxError(
            f"Expected {token_type}, got {self.tokens[self.pos][0]} at position {self.pos}"
        )

    def random_coordinates(self):
        """Generate random coordinates between -10 and 10."""
        return random.uniform(-10, 10), random.uniform(-10, 10)

    def check_collinearity(self, p1, p2, p3):
        """Check if three points are collinear using the area formula."""
        return abs(p1.x * (p2.y - p3.y) + p2.x * (p3.y - p1.y) + p3.x * (p1.y - p2.y)) == 0

    def parse_points(self):
        self.consume("PLACE")
        points = []
        while self.pos < len(self.tokens) and self.tokens[self.pos][0] == "POINT":
            self.consume("POINT")
            name = self.consume("ID")

            while self.pos < len(self.tokens) and self.tokens[self.pos][0] == "DOT":
                self.consume("DOT")

            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "LPAREN":
                self.consume("LPAREN")
                x = self.consume("NUMBER")
                self.consume("COMMA")
                y = self.consume("NUMBER")
                self.consume("RPAREN")
            else:
                x, y = self.random_coordinates()

            point = PointNode(name, x, y)
            self.built_points[name] = point
            points.append(point)

            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "DOT":
                self.consume("DOT")
                break
            if self.pos < len(self.tokens) and self.tokens[self.pos][0] == "COMMA":
                self.consume("COMMA")
        return points

    def parse_rectangle(self):
        self.consume("BUILD")
        self.consume("RECTANGLE")
        points = [self.consume("ID") for _ in range(4)]
        if any(name not in self.built_points for name in points):
            raise ValueError(f"One or more points are not defined: {points}")
        return RectangleNode([self.built_points[name] for name in points])

    def parse_triangle(self):
        self.consume("BUILD")
        self.consume("TRIANGLE")
        points = [self.consume("ID") for _ in range(3)]
        if any(name not in self.built_points for name in points):
            raise ValueError(f"One or more points are not defined: {points}")

        p1, p2, p3 = [self.built_points[name] for name in points]
        if self.check_collinearity(p1, p2, p3):
            raise ValueError(f"The points {points} are collinear and cannot form a triangle.")

        return TriangleNode([p1, p2, p3])

    def parse_line(self):
        self.consume("CONNECT")
        self.consume("LINE")
        point1 = self.consume("ID")
        self.consume("COMMA")
        point2 = self.consume("ID")
        if point1 not in self.built_points or point2 not in self.built_points:
            raise ValueError(f"One or more points are not defined: {point1}, {point2}")
        return LineNode(self.built_points[point1], self.built_points[point2])

    def parse(self):
        nodes = []
        while self.pos < len(self.tokens):
            token_type = self.tokens[self.pos][0]

            if token_type == "PLACE":
                nodes.extend(self.parse_points())
            elif token_type == "BUILD" and self.tokens[self.pos + 1][0] == "RECTANGLE":
                nodes.append(self.parse_rectangle())
            elif token_type == "BUILD" and self.tokens[self.pos + 1][0] == "TRIANGLE":
                nodes.append(self.parse_triangle())
            elif token_type == "CONNECT":
                nodes.append(self.parse_line())
            elif token_type == "DOT":
                self.consume("DOT")
                continue
            else:
                raise SyntaxError(f"Unexpected token: {token_type}")

        return nodes


def draw(nodes):
    for node in nodes:
        if isinstance(node, RectangleNode):
            points = node.points + [node.points[0]]
            x = [point.x for point in points]
            y = [point.y for point in points]
            plt.plot(x, y, label="Rectangle")
        elif isinstance(node, TriangleNode):
            points = node.points + [node.points[0]]
            x = [point.x for point in points]
            y = [point.y for point in points]
            plt.plot(x, y, label="Triangle")
        elif isinstance(node, LineNode):
            x = [node.point1.x, node.point2.x]
            y = [node.point1.y, node.point2.y]
            plt.plot(x, y, label="Line")

    for point in nodes:
        if isinstance(point, PointNode):
            plt.scatter(point.x, point.y, color='red')
            plt.text(point.x - 0.08, point.y + 0.1, f'{point.name}', fontsize=12)

    plt.legend()
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.show()


text = """
Поставити точку A (1,1), точку B (3,1), точку C (3,3), точку D (1,3).
Поставити точку E(6, 6), точку P, точку K (6, 7).
Побудувати прямокутник A B C D.
Провести відрізок B, E.
Побудувати трикутник A K E.
Провести відрізок A, P.
Поставити точку Q, точку W.
"""

lexer = Lexer(text)
tokens = lexer.tokenize()
print(tokens)
parser = Parser(tokens)
nodes = parser.parse()
draw(nodes)
