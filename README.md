# rachel-ai
Script Collection for the Rachel AI project.

## Project Setup with Poetry

This project uses [Poetry](https://python-poetry.org/) for dependency management and environment setup. Poetry simplifies package installation and ensures that all dependencies are managed consistently across environments.

### Prerequisites

Before setting up the project, make sure you have Poetry installed. You can install Poetry using the following command:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### How to Use

1. **Clone the repository**:

   ```bash
   git clone git@github.com:timullrich/rachel-ai.git
   cd rachel-ai
   ```

2. **Install dependencies**:

   After cloning the repository, install all required dependencies using Poetry:

   ```bash
   poetry install
   ```

   This command will create a virtual environment and install all dependencies specified in the `pyproject.toml` file.

3. **Activate the virtual environment**:

   If you want to activate the virtual environment created by Poetry, use the following command:

   ```bash
   poetry shell
   ```

4. **Run the project**:

   After activating the virtual environment, you can run any Python script in the project as usual:

   ```bash
   python your_script.py
   ```

### Adding Dependencies

If you need to add new dependencies to the project, you can use the following command:

```bash
poetry add <package_name>
```

This will automatically update the `pyproject.toml` and `poetry.lock` files to include the new package.

### Deactivating the Environment

To exit the Poetry shell (virtual environment), simply run:

```bash
exit
```

