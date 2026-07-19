# How to access GPUs

You cannot simply SSH into a GPU node. GPU access must be requested through LSF. Minerva’s GPU resources are available through the `gpu`, `gpuexpress`, and limited `interactive` queues.

The essential options are:

\-P acc\_PROJECT        your allocation account  
\-q gpu                GPU queue  
\-gpu "num=1"          number of GPUs requested per node  
\-R a100               requested GPU model  
\-R "span\[hosts=1\]"    keep all CPUs and GPUs on one node  
\-n 4                  number of CPU cores  
\-W 01:00              maximum runtime

### **Interactive GPU session**

First find your allocation:

mybalance

Then request an interactive shell on one A100 GPU:

bsub \\  
  \-P acc\_YOURPROJECT \\  
  \-q gpu \\  
  \-n 4 \\  
  \-R a100 \\  
  \-R "span\[hosts=1\]" \\  
  \-R "rusage\[mem=8000\]" \\  
  \-gpu "num=1" \\  
  \-W 01:00 \\  
  \-Is /bin/bash

Replace `acc_YOURPROJECT` with an account shown by `mybalance`.

This request means:

* 1 A100 GPU;  
* 4 CPU cores;  
* 8 GB RAM per CPU core, or 32 GB total;  
* all resources on one machine;  
* one-hour maximum runtime.

Once the job starts and the prompt returns, verify that you are on a GPU node:

hostname  
echo "$CUDA\_VISIBLE\_DEVICES"  
nvidia-smi

`nvidia-smi` is expected to work only after the GPU job is running on a GPU node. LSF automatically sets `CUDA_VISIBLE_DEVICES` to the GPU assigned to your job; do not manually replace that variable.

Check available CUDA versions:

module avail cuda  
module avail cudnn

Load a CUDA version only when your application or environment requires it:

module load cuda/\<VERSION\>

Then activate your Python environment. For example:

module load miniforge3/\<VERSION\>  
source activate my\_environment

For PyTorch:

python \-c 'import torch; print("CUDA available:", torch.cuda.is\_available()); print(torch.cuda.get\_device\_name(0))'

For TensorFlow:

python \-c 'import tensorflow as tf; print(tf.config.list\_physical\_devices("GPU"))'

The interactive GPU command and available CUDA modules are documented by Minerva’s GPU guide.

Exit when finished:

exit

That releases the GPU.

---

## **A batch GPU-job example**

Create a file named `gpu_job.lsf`:

\#\!/bin/bash

\#BSUB \-J gpu\_training  
\#BSUB \-P acc\_YOURPROJECT  
\#BSUB \-q gpu  
\#BSUB \-n 4  
\#BSUB \-R "rusage\[mem=8000\]"  
\#BSUB \-R "span\[hosts=1\]"  
\#BSUB \-R a100  
\#BSUB \-gpu "num=1"  
\#BSUB \-W 04:00  
\#BSUB \-oo %J.out  
\#BSUB \-eo %J.err  
\#BSUB \-L /bin/bash

\# Run from the directory where the job was submitted.  
cd "$LS\_SUBCWD"

module purge

\# Replace this with the Miniforge version you use.  
module load miniforge3/\<VERSION\>  
source activate my\_environment

\# Load CUDA only if required by your environment/application.  
\# module load cuda/\<VERSION\>

nvidia-smi  
python train.py

Submit it from the login node:

bsub \< gpu\_job.lsf

The submission response will contain a job ID:

Job \<123456789\> is submitted to queue \<gpu\>.

Monitor it with:

bjobs  
bjobs \-l 123456789

View output while it is running:

bpeek 123456789

Cancel it:

bkill 123456789

After completion, inspect GPU utilization:

bjobs \-l \-gpu 123456789

For an older completed job:

bhist \-l \-gpu 123456789

Minerva collects GPU utilization, peak GPU memory, execution time, and related metrics through NVIDIA DCGM.

## **Choosing the GPU model**

Use one of these LSF resource names:

| Request | GPU |
| ----- | ----- |
| `-R v100` | V100, 16 GB |
| `-R a100` | A100, 40 GB |
| `-R a10080g` | A100, 80 GB |
| `-R h10080g` | H100 PCIe, 80 GB |
| `-R h100nvl` | H100 SXM/NVLink, 80 GB |
| `-R l40s` | L40S, 48 GB |
| `-R b200` | B200, 192 GB |

For an initial job, `a100` is a reasonable choice. Use an 80 GB GPU only when the model or batch size needs the additional memory. Minerva recommends A100 or H100 for typical one- or two-GPU jobs; the B200 systems are intended for large, high-memory, multi-GPU workloads.

## **The most common GPU mistakes**

1. **Running `nvidia-smi` on the login node.** It becomes available after an allocated GPU job starts.  
2. **Forgetting `span[hosts=1]`.** The `num=` value is per node. Without `span[hosts=1]`, CPUs can potentially be spread over several nodes, reserving more GPUs than the program can use.  
3. **Requesting too many GPUs immediately.** Start with one GPU and a small test dataset; larger requests generally wait longer in the queue.  
4. **Changing `CUDA_VISIBLE_DEVICES`.** LSF sets this correctly for the allocated cards.  
5. **Assuming `-R rusage[mem=8000]` means 8 GB total.** Memory is per CPU core. With `-n 4`, that request reserves approximately 32 GB.

A practical setup is therefore: **Open OnDemand Code Server for editing, an interactive one-GPU job for debugging, and an LSF batch script for full training runs.**


