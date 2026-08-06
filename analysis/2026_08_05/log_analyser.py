
FILE = "Clock_synchronization_Analysis.txt"


class LogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file

    def analyze(self):
        with open(self.log_file, 'r') as f:
            lines = f.readlines()

        clock_offset_samples = []
        for line in lines:
            if "Clock offset established" in line:
                clock_offset_value = float(line.split()[9].replace("ms", ""))
                clock_offset_samples.append(clock_offset_value)

        if clock_offset_samples:
            # print max and min clock offset values
            average_offset = sum(clock_offset_samples) / len(clock_offset_samples)
            print(f"Average Clock Offset: {average_offset:.2f} ms")
            print(f"Max Clock Offset: {max(clock_offset_samples):.2f} ms")
            print(f"Min Clock Offset: {min(clock_offset_samples):.2f} ms")



def main():
    print("Log Analyser")
    analyzer = LogAnalyzer(FILE)
    analyzer.analyze()


if __name__ == "__main__":
    main()