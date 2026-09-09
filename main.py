from core.Beam import Load

def main():

    l= [
        lambda x: -2,
        lambda x: -x**2,
        lambda x: -x**3,
    ]
    for fun in l:
        load1 = Load(0,300, fun)
        print(load1.get_average_value())
        print(load1.get_avg_value_point())


if __name__ == "__main__":
    main()
