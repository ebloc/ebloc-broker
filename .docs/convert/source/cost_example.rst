Cost Model
==========

A cost model for sequential cloud computing should consider a
pay-per-use model. In our work we presented a cost model, which
calculates how much USDT token the requester has to pay for the use of
the pay to run a job through eBlocBroker on a provider for utilizing its
CPU cores and storage. Note that our cost model is implemented within
the smart contract. To calculate the total cost of the computational and
data resource on each provider, the following units of work are
considered: *core-minute*, *storage-hour*, *cache-megabyte*, and
*transfer-megabyte*. These unit of currencies are defined as follows:

1. A *core-minute* (:math:`F^{\mu}`) is the price for the use of a core
   per minute. The execution of the job as computation is charged at the
   rate of by minute they are executed. The calculated computational
   cost is defined as :math:`c^{\mu}`.

   For example, with 60 *core-minutes*, requester can run a job on the
   provider for period of 60 minutes on one core or for 15 minutes on 4
   CPU cores. In addition, running 128 CPU cores for 100 minutes will
   cost 12,800 *core-minutes*.

2. A *storage-hour* (:math:`F^{w}`) is the price for the use of
   long-term storage a MB per hour. The storage of the dataset is
   charged at the rate of by hour they are stored. The calculated
   storage cost is defined as :math:`c^{w}`.

   Time available on the provider’s storage resource is denominated in
   *storage-hours*. For example, with 1000 *storage-hours*, requester
   can store a data file on the provider for 1 GB per hour or 500 MB per
   2 hours, and so on.

3. A *cache-megabyte* (:math:`F^{k}`) is the price for the use of
   storage used in MB to store a data file temporarily on a provider’s
   storage until its corresponding job is complete its execution. The
   calculated cache cost is defined as :math:`c^{k}`.

   The amount of storage in MB on the provider’s temporary storage
   resource is denominated in *cache-megabytes*. During data file’s
   corresponding job is still running, if the data owner requests to use
   the same temporarily stored data file, then the storage cost will be
   applied again. For example, with 500 *cache-megabytes*, requester can
   store a 500 MB data file on the provider.

4. A *transfer-megabyte* (:math:`F^{\tau}`) is the price for the use of
   bandwidth used in MB to transfer data in between the provider and the
   cloud storage facility. The calculated data transfer cost is defined
   as :math:`c^{\tau}`.

   The amount of bandwidth used in MB is denominated in
   *transfer-megabytes*. For example, with 500 *transfer-megabytes*, the
   requester can send a 500 MB data file through a cloud storage
   facility.

5. A fee (:math:`F^{m}`) to use data file set by the provider.

Example
-------

Provider register itself with following file containing its prices:

.. container:: minted

   yaml prices: price_core_min: "0.001 usd" price_data_transfer: "0.0001
   cent" price_storage: "0.0001 cent" price_cache: "0.0001 cent"

.. container::
   :name: tab-cost

   .. table:: Description of prices on provider :math:`n`.

      +-----------+-----------+-----------+-----------+-----------+---+---+
      | **p       | :         | :math:`F  | :math:`F  | :m        |   |   |
      | rovider** | math:`F_{ | _{n}^{w}` | _{n}^{k}` | ath:`F_{n |   |   |
      |           | n}^{\mu}` |           |           | }^{\tau}` |   |   |
      +-----------+-----------+-----------+-----------+-----------+---+---+
      |           | (usd)     | (cent)    | (cent)    | (cent)    |   |   |
      +-----------+-----------+-----------+-----------+-----------+---+---+
      | n         | 0.001     | 0.0001    | 0.0001    | 0.0001    |   |   |
      +-----------+-----------+-----------+-----------+-----------+---+---+

.. container::
   :name: tab-cost

   .. table:: Description of fees of the datasets on provider :math:`n`.

      ================================ ==============
      **dataset**                      F_n^{m} (cent)     
      dd0fbccccf7a198681ab838c67b68fbf 0.2                
      45281dfec4618e5d20570812dea38760 0.2                
      ================================ ==============

A requester is willing to submit a job requesting:

-  1 core for 60 minutes, which will cost 0.06 usd.

-  4 datasets and for 100 MB

   (A) size= 9 MB

   (B) size=1000 MB, storageDuration=10 hours.

   (C) dd0fbccccf7a198681ab838c67b68fbf

   (D) 45281dfec4618e5d20570812dea38760

.. container::
   :name: tab-cost

   .. table:: Description of prices on provider :math:`n`.

      ======== ============= ============= ================
      **data** :math:`c^{w}` :math:`c^{k}` :math:`c^{\tau}`   
      A        0             0.0009        0.0009             
      B        1             0             0.1                
      C        0.2           0             0                  
      D        0.2           0             0                  
      sum      1.04          0.0009        0.1009             
      ======== ============= ============= ================

Note that, first these are calculated costs in the *submitJob()*
function through smart contracts. For example, afterwards if the exact
same job submitted within 10 hours, which is the storage duration for
dataset :math:`B`), no storage, cache would be paid for data :math:`B`.

Process Payment
---------------

When the job is completed assume following usage is provided by the
provider to *processPayment()*. Note that size of the downloaded data
files might be much smaller than the requested amount since they
submitted compressed.

-  Executed run time of the job is 7 minutes. Gained amount is 0.007 usd
   and 0.053 usd is refunded (unused 53 minutes).

-  Size of sum of the downloaded data files is 800 MB and calculated
   data size to be uploaded is 50 MB Here for data transferring cost
   gained amount is 0.085 cent and 0.02009 cent is refunded. This will
   cover data transfer cost for :math:`A` and :math:`B`

-  Estimate file space usage for :math:`A` is 5 MB. Here the cache cost
   gained amount is 0.0005 cent and 0.0004 cent is refunded. Since
   storage cost is already paid for data file :math:`B` no cache cost is
   applied.

-  Gain 0.4 cent for the usage of the datasets :math:`C` and :math:`D`,
   0.2 cent each.
