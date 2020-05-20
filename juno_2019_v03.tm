KPL/MK

   This meta-kernel lists the JUNO SPICE kernels providing coverage for
   2018. All of the kernels listed below are archived in the JUNO SPICE
   data set (DATA_SET_ID = "JNO-J/E/SS-SPICE-6-V1.0"). This set of
   files and the order in which they are listed were picked to provide
   the best available data and the most complete coverage for the
   specified year based on the information about the kernels available
   at the time this meta-kernel was made. For detailed information
   about the kernels listed below refer to the internal comments
   included in the kernels and the documentation accompanying the JUNO
   SPICE data set.

   It is recommended that users make a local copy of this file and
   modify the value of the PATH_VALUES keyword to point to the actual
   location of the JUNO SPICE data set's ``data'' directory on their
   system. Replacing ``/'' with ``\'' and converting line terminators
   to the format native to the user's system may also be required if
   this meta-kernel is to be used on a non-UNIX workstation.
 
   This file was created on April 2, 2020 by Boris Semenov, NAIF/JPL.
   The original name of this file was juno_2019_v03.tm.

   \begindata

      PATH_VALUES     = ( './data' )

      PATH_SYMBOLS    = ( 'KERNELS' )

      KERNELS_TO_LOAD = (

                       '$KERNELS/lsk/naif0012.tls'

                       '$KERNELS/pck/pck00010.tpc'

                       '$KERNELS/sclk/jno_sclkscet_00098.tsc'

                       '$KERNELS/fk/juno_v12.tf'

                       '$KERNELS/spk/juno_rec_181126_190118_190124.bsp'
                       '$KERNELS/spk/juno_rec_190118_190312_190319.bsp'
                       '$KERNELS/spk/juno_rec_190312_190504_190509.bsp'
                       '$KERNELS/spk/juno_rec_190504_190626_190627.bsp'
                       '$KERNELS/spk/juno_rec_190626_190817_190822.bsp'
                       '$KERNELS/spk/juno_rec_190817_191010_191022.bsp'
                       '$KERNELS/spk/juno_rec_170106_170228_170307.bsp'
                       '$KERNELS/spk/juno_rec_170228_170422_170427.bsp'

                        )

   \begintext

End of MK.
