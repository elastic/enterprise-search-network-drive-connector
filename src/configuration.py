class Configuration:
    """This class is used to create an instance of Configuration only if there is no instance created so far;
        otherwise, it will return the instance that is already created which contains all configurations placed
        inside the configuration file with validation
    """

    def validate(self):
        """Validates each properties defined in the yaml configuration file
        """
