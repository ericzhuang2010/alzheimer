# How to log in 

step1: https://mshmsvpn.mssm.edu/my.policy

Step2: skip inspection

Step3: log in zhuane01@mssm.edu   HappyKids2026\!\!\!

Step4: ssh zhuane01@minerva.hpc.mssm.edu

/sc/arion/work/zhuane01  
/hpc/users/zhuane01

# Kill processes

This may happen if you have lots of processes open on the login node from applications like VS Code. You can use the 'pstree' command to check and the 'pkill' command to terminate the processes you own on the node. Please let me know if you want me to kill the running processes for you.

$ pstree minervaUserID

$ pkill \-u minervaUserID \# To terminate all the processes.

$ kill processID \# To terminate a single process

\* We recommend Globus for the file transfer. Please check below.

https://labs.icahn.mssm.edu/minervalab/documentation/file-transfer-globus/

# Ollama

[https://labs.icahn.mssm.edu/minervalab/documentation/ollama/](https://labs.icahn.mssm.edu/minervalab/documentation/ollama/)

\====================================================  
The snRNA-seq dataset you will use (described attached paper) is available from Minerva at /sc/arion/projects/zhangb03a/shared/ROSMAP/Synapse/snRNAseq\_MIT/GeneExpression/10x/processed

Due to the large data size, the dataset has been splitted into multiple R/Seurat objects in RDS files by cell type. The dataset has been quality controlled (QCed) by the original study. However, only the raw counts are included in each R/Seurat. You need to do normalization using NormalizeData from R/Seurat package before any down stream analysis. You may find some reference data analysis code from https://github.com/songw01/AD\_scRNAseq\_companion

# IDE

The official portal explicitly offers Code Server, Jupyter Server with optional GPU accelerators, and RStudio Server.

When off campus, connect to the Mount Sinai VPN. New users must log in through SSH at least once so Minerva creates the home directory:

ssh YOUR\_USERID@minerva.hpc.mssm.edu

Minerva currently uses Microsoft Azure MFA for SSH authentication.

Then open:

[https://ondemand.hpc.mssm.edu](https://ondemand.hpc.mssm.edu)

Log in and select:

Interactive Apps → Code Server

You will be asked for a project/allocation account, cores, memory, and session duration. To find your valid project account, run in a ssh session:

mybalance

  zhuane01       acc\_adineto                   Yes

  zhuane01       acc\_zhangb03a                 Yes

New home directories must be initialized through SSH before Open OnDemand will work.

### **Recommended development pattern**

Use Code Server or JupyterLab to:

* edit code;  
* test on small data;  
* debug;  
* prepare LSF submission scripts.

Use a batch job for long model training, large datasets, or production analysis. Minerva’s login nodes are only for editing, compilation, file management, and job submission—not computational jobs.

For Python environments, Minerva’s current documentation recommends **Miniforge**, rather than copying older examples that use Anaconda:

module spider miniforge3  
module load miniforge3/\<VERSION\>  
source activate my\_environment

Minerva recommends placing Conda environments and package caches under `/sc/arion/work/...`, rather than your quota-limited home directory.

---

# Where to put code and data

For a project with **a lot of data or many files**, use a Minerva **project directory** as the main location for datasets and results:

/sc/arion/projects/\<project\_acronym\>/\<your\_project\>

Do **not** use your home directory as the main data directory, and do not use scratch as permanent storage.

## **How Minerva’s storage areas should be used**

| Location | Recommended use |
| ----- | ----- |
| `/hpc/users/$USER` | Configuration files, SSH files, small scripts |
| `/sc/arion/work/$USER` | Code, Conda environments, package caches, small personal working files |
| `/sc/arion/projects/<project>` | Large datasets, processed data, model checkpoints, and results |
| `/sc/arion/scratch/$USER` | Temporary intermediate files that can be deleted |

Your home directory has a 30 GB quota and is backed up, but it is relatively slow. Your personal work directory is faster and has a 100 GB quota, but is not backed up. Project storage is intended for larger project allocations and is not purged, but it is also not backed up. Scratch storage is temporary, not backed up, and files are automatically eligible for deletion after 14 days.

## **Recommended directory layout**

A good setup separates **code**, **large data**, and **temporary files**:

export PROJECT\_ID=your\_project\_acronym  
export STUDY=my\_analysis

export CODE=/sc/arion/work/$USER/$STUDY  
export DATA=/sc/arion/projects/$PROJECT\_ID/$STUDY  
export SCRATCH=/sc/arion/scratch/$USER/$STUDY

Create the directories:

mkdir \-p "$CODE"

mkdir \-p "$DATA"/data/raw  
mkdir \-p "$DATA"/data/processed  
mkdir \-p "$DATA"/results  
mkdir \-p "$DATA"/checkpoints  
mkdir \-p "$DATA"/logs

mkdir \-p "$SCRATCH"/staging  
mkdir \-p "$SCRATCH"/tmp

The resulting structure would be:

/sc/arion/work/your\_username/my\_analysis/  
└── code and software files

/sc/arion/projects/your\_project\_acronym/my\_analysis/  
├── data/  
│   ├── raw/  
│   └── processed/  
├── results/  
├── checkpoints/  
└── logs/

/sc/arion/scratch/your\_username/my\_analysis/  
├── staging/  
└── tmp/

### **Where to point your IDE**

In Code Server, VS Code, or another IDE, open:

/sc/arion/work/$USER/my\_analysis

Keep the large data directory **outside the IDE workspace**. This prevents the IDE from trying to index, search, and watch thousands or millions of data files, which is a common cause of VS Code slowness or remote-connection problems.

Your code can refer to the project data with an absolute path:

from pathlib import Path

PROJECT \= Path("/sc/arion/projects/your\_project\_acronym/my\_analysis")  
RAW\_DATA \= PROJECT / "data" / "raw"  
PROCESSED\_DATA \= PROJECT / "data" / "processed"  
RESULTS \= PROJECT / "results"

A more portable approach is to read the path from an environment variable:

import os  
from pathlib import Path

PROJECT \= Path(os.environ\["PROJECT\_DATA"\])  
RAW\_DATA \= PROJECT / "data" / "raw"  
RESULTS \= PROJECT / "results"

Set it before running the program:

export PROJECT\_DATA=/sc/arion/projects/$PROJECT\_ID/$STUDY  
python train.py

In an LSF job script, use the same separation:

\#\!/bin/bash  
\#BSUB \-J my\_training  
\#BSUB \-P acc\_YOURPROJECT  
\#BSUB \-q gpu  
\#BSUB \-n 4  
\#BSUB \-R "rusage\[mem=8000\]"  
\#BSUB \-R "span\[hosts=1\]"  
\#BSUB \-R a100  
\#BSUB \-gpu "num=1"  
\#BSUB \-W 04:00  
\#BSUB \-oo /sc/arion/projects/PROJECT\_ID/my\_analysis/logs/%J.out  
\#BSUB \-eo /sc/arion/projects/PROJECT\_ID/my\_analysis/logs/%J.err

export CODE=/sc/arion/work/$USER/my\_analysis  
export PROJECT\_DATA=/sc/arion/projects/PROJECT\_ID/my\_analysis  
export JOB\_SCRATCH=/sc/arion/scratch/$USER/my\_analysis/$LSB\_JOBID

mkdir \-p "$JOB\_SCRATCH"

cd "$CODE"  
python train.py

\# Delete disposable job-specific files when successful.  
rm \-rf "$JOB\_SCRATCH"

Replace both `PROJECT_ID` entries and `acc_YOURPROJECT`.

## **Find your available project directory**

Run:

groups  
showquota \-u "$USER"

For a particular project:

showquota \-p PROJECT\_ID  
ls \-ld /sc/arion/projects/PROJECT\_ID

Minerva’s `showquota` command reports work, scratch, and project usage. Project directory access is controlled through the project’s Unix group; the PI or project delegate manages membership and requests storage increases.

If you receive:

Permission denied

do not use:

chmod \-R 777 ...

Instead, ask your PI or project delegate to confirm that your Minerva username has been added to the project.

## **Important rules for large datasets**

### **Do not put permanent data in scratch**

Scratch is appropriate for:

* temporary extracted files;  
* downloaded staging copies;  
* temporary training shards;  
* disposable intermediate results;  
* files that can be recreated.

Anything that must survive should be copied to:

/sc/arion/projects/\<project\_acronym\>

Minerva documents a 14-day scratch purge policy, so scratch should never contain the only copy of raw data, trained models, or final results.

### **Be careful with millions of small files**

Arion is GPFS/Spectrum Scale. It supports large parallel workloads, but directory operations such as creating, listing, renaming, or deleting enormous numbers of individual files can become slow.

For many small files:

* Divide them into subdirectories by sample, patient, date, or batch.  
* Avoid placing millions of files in one directory.  
* Do not open the data directory directly in Code Server.  
* Consider Parquet for tables, HDF5/Zarr for arrays, or tar shards for training images when your software supports those formats.  
* Avoid running `ls -l` recursively over very large directories.

For example:

data/raw/  
├── batch\_001/  
├── batch\_002/  
├── batch\_003/  
└── batch\_004/

is usually easier to manage than:

data/raw/  
└── 5,000,000 files in one directory

### **Transfer large datasets with Globus**

For large or restartable transfers, use Minerva’s Globus service rather than uploading through Code Server or relying on one long `scp` session. Minerva provides Globus collections that access both `/sc/arion` and `/hpc/users`.

## **Back up important files**

Only the small home directory is backed up. Work and project storage are not backups, even though they are not routinely purged. Therefore:

* Keep code in Git or another approved source-control system.  
* Preserve the original authoritative copy of raw data.  
* Archive irreplaceable project data using Minerva’s approved archival mechanism, such as TSM/Spectrum Protect.

For NIH controlled-access genomic data, confirm the required environment before transferring anything: Mount Sinai’s Minerva-Res environment is specifically designed for approved controlled-access genomic projects and uses different encrypted project paths.

**The practical recommendation is:** open `/sc/arion/work/$USER/<study>` in your IDE, store large data and final outputs under `/sc/arion/projects/<project>/<study>`, and use `/sc/arion/scratch/$USER/<study>` only for disposable temporary files.

