import os

from lib import PROGRAM_PATH, CacheType, generate_md5_sum, log


class Storage(object):
    def __init__(self, loggedJob, jobInfo, requesterID, is_already_cached, oc=None):
        self.requesterID = requesterID
        self.jobInfo = jobInfo
        self.loggedJob = loggedJob
        self.job_key = self.loggedJob.args["jobKey"]
        self.index = self.loggedJob.args["index"]
        self.jobID = 0
        self.cache_type = loggedJob.args["cacheType"]
        self.dataTransferIn = jobInfo[0]["dataTransferIn"]
        self.is_already_cached = is_already_cached
        self.source_code_hashes = loggedJob.args["sourceCodeHash"]
        self.job_key_list = []
        self.md5sum_dict = {}
        self.folder_path_to_download = {}
        self.oc = oc
        self.cloudStorageID = loggedJob.args["cloudStorageID"]
        self.results_folder_prev = f"{PROGRAM_PATH}/{self.requesterID}/{self.job_key}_{self.index}"
        self.results_folder = f"{self.results_folder_prev}/JOB_TO_RUN"
        self.private_dir = f"{PROGRAM_PATH}/{requesterID}/cache"
        self.public_dir = f"{PROGRAM_PATH}/cache"
        self.folder_type_dict = {}

        if not os.path.isdir(self.private_dir):
            os.makedirs(self.private_dir)

        if not os.path.isdir(self.public_dir):
            os.makedirs(self.public_dir)

        if not os.path.isdir(self.results_folder):
            os.makedirs(self.results_folder)

    def whoami(self):
        return type(self).__name__

    def is_md5sum_matches(self, path, name, id, folder_type, cache_type):
        res = generate_md5_sum(path)
        if res == name:
            # Checking is already downloaded folder's hash matches with the given hash
            if self.whoami() == "EudatClass" and folder_type != "":
                self.folder_type_dict[name] = folder_type

            self.cache_type[id] = cache_type

            if cache_type == CacheType.PUBLIC.value:
                self.folder_path_to_download[name] = self.public_dir
                log(f"{name} is already cached under the public directory...", "blue")
            elif cache_type == CacheType.PRIVATE.value:
                self.folder_path_to_download[name] = self.private_dir
                log(f"{name} is already cached under the private directory...", "blue")

            return True

        return False

    def is_cached(self, name, id):
        status = False
        if self.cache_type[id] == CacheType.PRIVATE.value:
            # First checking does is already exist under public cache directory
            cached_folder = f"{self.public_dir}/{name}"
            cached_tar_file = f"{cached_folder}.tar.gz"

            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    status = self.is_md5sum_matches(cached_folder, name, id, "folder", CacheType.PUBLIC.value)
            else:
                if self.whoami() == "EudatClass":
                    self.folder_type_dict[name] = "tar.gz"

                status = self.is_md5sum_matches(cached_tar_file, name, id, "", CacheType.PUBLIC.value)
        else:
            # First checking does is already exist under the requesting user's private cache directory
            cached_folder = self.private_dir
            cached_folder = f"{self.private_dir}/{name}"
            cached_tar_file = f"{cached_folder}.tar.gz"

            if not os.path.isfile(cached_tar_file):
                if os.path.isfile(f"{cached_folder}/run.sh"):
                    status = self.is_md5sum_matches(cached_folder, name, id, "folder", CacheType.PRIVATE.value)
            else:
                if self.whoami() == "EudatClass":
                    self.folder_type_dict[name] = "tar.gz"
                status = self.is_md5sum_matches(cached_tar_file, name, id, "", CacheType.PRIVATE.value)

        return status
