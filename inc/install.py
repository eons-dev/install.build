import os
import logging
import shutil
import eons
from pathlib import Path
from ebbs import Builder

class install(Builder):
	def __init__(this, name="Install"):
		super().__init__(name)

		this.functionSucceeded = True
		this.rollbackSucceeded = True
		this.enableRollback = True

		this.requiredKWArgs.append("paths")

		this.optionalKWArgs["project_path"] = None
		this.optionalKWArgs["installed_at"] = None

		this.result = eons.util.DotDict()


	# Reset result before each call.
	def Initialize(this):
		this.result = eons.util.DotDict()
		super().Initialize()


	# Required Merx method. See that class for details.
	def Build(this):
		if (not this.project_path):
			this.functionSucceeded = False
			return this.result

		logging.info(f"Installing {this.projectName}...")
		
		installedObjects = []

		# Assume this.paths are all valid.
		# The dictionary this.paths comes from EMI
		for target, destination in this.paths.items():
			
			# Going to each potential target
			candidate = this.project_path.joinpath(target)

			# Check whether target exists as part of Epitome
			if (not candidate.exists()):
				continue
			
			logging.debug(f"Copying files from {candidate} to {destination}")
			#Go down every path in target and look for things
			for thing in candidate.iterdir():

				# Create variable of path of thing, but within destination path structure
				expectedResult = Path(destination).joinpath(thing.relative_to(candidate)).resolve()

				# Track paths of things expected to exist within destination path structure 
				installedObjects.append(str(expectedResult))

				# Redefine thing to its absolute path
				thing = thing.resolve()
				logging.debug(f"Copying {str(thing)}.")

				#Depending on whether thing is a directory or file, use appropriate shutil function to copy the Epitome targets to appropriate place within destination file structure
				if (thing.is_dir()):
					try:
						shutil.copytree(str(thing), expectedResult)
					except shutil.Error as exc:
						errors = exc.args[0]
						for error in errors:
							src, dst, msg = error
							logging.debug(f"{msg}")
				else: #thing is file
					try:
						shutil.copy(str(thing), expectedResult)
					except shutil.Error as exc:
						errors = exc.args[0]
						for error in errors:
							src, dst, msg = error
							logging.debug(f"{msg}")

				# Check whether the copy was successful
				if (not expectedResult.exists()):
					logging.error(f"COULD NOT FIND {str(expectedResult)}! Will rollback.")
					this.functionSucceeded = False
				logging.debug(f"Created {str(expectedResult)}.")

				# Add approriate permissions to the bin and exe targets
				if (target in ["bin", "exe"]):
					logging.debug(f"Adding execute permissions to {str(expectedResult)}.")
					expectedResult.chmod(0o755)


		if (this.functionSucceeded):
			this.result.installed_at = ";".join(installedObjects)
			if (not os.geteuid()): #root = uid 0
				logging.debug(f"Updating library paths.")
				this.RunCommand(f"ldconfig {Path(this.paths['lib']).resolve()}")
				
		return this.result
			

	# Required Merx method. See that class for details.
	def Rollback(this):
		logging.info(f"Removing {this.projectName}...")
		if (this.installed_at is None or this.installed_at is None or not len(this.installed_at)):
			logging.debug(f"Nothing to remove for {this.projectName}")
			return this.result
		
		toRemove = this.installed_at.split(';')
		for thing in toRemove:
			logging.debug(f"REMOVING: {thing}")
			thing = Path(thing)
			if (not thing.exists()):
				logging.debug(f"Could not find {str(thing)}")
				#That's okay. that might be why we're rolling back ;)
				continue
			if (thing.is_dir()):
				shutil.rmtree(thing)
			else:
				thing.unlink()
			logging.debug(f"Removed {str(thing)}")
			
			#TODO: error checking
	
		this.result.installed_at = ""
		super().Rollback()
		return this.result