### Python Generators

This is a simple example of using generators in Python. It is based on the [Python Generators](https://www.w3schools.com/python/python_generators.asp) tutorial on W3Schools.

The code is divided into two files:

- `seed.py` contains the code to create the database and the table, and to insert data into the table.
- `generator.py` contains the code to generate the data.

To run the code, open a terminal, navigate to the directory containing the files, and run the following command:

```bash
python seed.py
```

This will create the database and the table, and insert data into the table.

To generate the data, run the following command:

```bash
python generator.py
```

This will generate the data and print it to the console.

Note that the `generator.py` file contains a `main()` function that calls the `generate_data()` function. This function is responsible for generating the data and printing it to the console. The `generate_data()` function uses a generator to generate the data. The generator is defined in the `generate_data()` function and is called using the `yield` keyword. The `yield` keyword is used to return a value from a generator function. When the `yield` keyword is used, the function returns a generator object, which can be used to iterate over the values returned by the generator.