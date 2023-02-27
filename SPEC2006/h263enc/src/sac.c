/************************************************************************
 *
 *  sac.c, part of tmn (TMN encoder)
 *  Copyright (C) 1996  Telenor R&D, Norway
 *        Karl Olav Lillevold <Karl.Lillevold@nta.no>
 *
 *  This program is free software; you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation; either version 2 of the License, or
 *  (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 *
 *  You should have received a copy of the GNU General Public License
 *  along with this program; if not, write to the Free Software
 *  Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
 *
 *  Karl Olav Lillevold               <Karl.Lillevold@nta.no>
 *  Telenor Research and Development
 *  P.O.Box 83                        tel.:   +47 63 84 84 00
 *  N-2007 Kjeller, Norway            fax.:   +47 63 81 00 76
 *
 *  Robert Danielsen                  e-mail: Robert.Danielsen@nta.no
 *  Telenor Research and Development  www:    http://www.nta.no/brukere/DVC/
 *  P.O.Box 83                        tel.:   +47 63 84 84 00
 *  N-2007 Kjeller, Norway            fax.:   +47 63 81 00 76
 *  
 ************************************************************************/
/*********************************************************************
 *
 * SAC Encoder Module
 * Algorithm as specified in H263 (Annex E)
 *         (c) BT Labs 1995
 *
 * Author: Pat Mulroy <pmulroy@visual.bt.co.uk>
 *
 *********************************************************************/

#include <stdio.h>
#include "sim.h"

#define   q1    16384
#define   q2    32768
#define   q3    49152
#define   top   65535

static long   low=0, high=top, opposite_bits=0, length=0, zerorun=0;

/*********************************************************************
 *
 *      Name:           AR_Encode
 *
 *      Description:    Encodes a symbol using syntax based arithmetic
 *        coding. Algorithm specified in H.263 (Annex E).
 *
 *      Input:          Array holding cumulative frequency data.
 *        Index into specific cumulative frequency array.
 *                      Static data for encoding endpoints.
 *
 *      Returns:        Number of bits used while encoding symbol.
 *
 *      Side Effects:   Modifies low, high, length and opposite_bits
 *        variables.
 *
 *      Author:         pmulroy@visual.bt.co.uk
 *
 *********************************************************************/

int AR_Encode(int index, int cumul_freq[ ])
{
  int bitcount=0;

  if (index<0) 
    return -1; /* Escape Code */

  length = high - low + 1;
  high = low - 1 + (length * cumul_freq[index]) / cumul_freq[0];
  low += (length * cumul_freq[index+1]) / cumul_freq[0];

  for ( ; ; ) {
    if (high < q2) {
      bitcount+=bit_opp_bits(0);
    }
    else if (low >= q2) {
      bitcount+=bit_opp_bits(1);	
      low -= q2; 
      high -= q2;
    }
    else if (low >= q1 && high < q3) {
      opposite_bits += 1; 
      low -= q1; 
      high -= q1;
    }
    else break;
 
    low *= 2; 
    high = 2*high+1;
  }
  return bitcount;
}

int bit_opp_bits(int bit) /* Output a bit and the following opposite bits */              
{                                   
  int bitcount=0;

  bitcount = bit_in_psc_layer(bit);

  while(opposite_bits > 0){
    bitcount += bit_in_psc_layer(!bit);
    opposite_bits--;
  }
  return bitcount;
}

/*********************************************************************
 *
 *      Name:           encoder_flush
 *
 *      Description:    Completes arithmetic coding stream before any
 *        fixed length codes are transmitted.
 *
 *      Input:          None
 *
 *      Returns:        Number of bits used.
 *
 *      Side Effects:   Resets low, high, zerorun and opposite_bits 
 *        variables.
 *
 *      Author:         pmulroy@visual.bt.co.uk
 *
 *********************************************************************/

int encoder_flush()
{
  int bitcount = 0;

  if (trace)
    fprintf(tf, "encoder_flush:\n");

  opposite_bits++;
  if (low < q1) {
    bitcount+=bit_opp_bits(0);
  }
  else {
    bitcount+=bit_opp_bits(1);
  }
  low = 0; 
  high = top;

  zerorun=0;

  return bitcount;
}

/*********************************************************************
 *
 *      Name:           bit_in_psc_layer
 *
 *      Description:    Inserts a bit into output bitstream and avoids
 *        picture start code emulation by stuffing a one
 *        bit.
 *
 *      Input:          Bit to be output.
 *
 *      Returns:        Nothing
 *
 *      Side Effects:   Updates zerorun variable.
 *
 *      Author:         pmulroy@visual.bt.co.uk
 *
 *********************************************************************/

int bit_in_psc_layer(int bit)
{
  void putbits (int, int);
  int bitcount = 0;

  if (zerorun > 13) {
    if (trace)
      fprintf(tf, "PSC emulation ... Bit stuffed.\n");
    putbits (1, 1);
    bitcount++;
    zerorun = 0;
  }

  putbits (1, bit);
  bitcount++;

  if (bit)
    zerorun = 0;
  else
    zerorun++;

  return bitcount;
}

/*********************************************************************
 *
 *      Name:           indexfn
 *
 *      Description:    Translates between symbol value and symbol
 *        index.
 *
 *      Input:          Symbol value, index table, max number of
 *        values.
 *
 *      Returns:        Index into cumulative frequency tables or
 *        escape code.
 *
 *      Side Effects:   none
 *
 *      Author:         pmulroy@visual.bt.co.uk
 *
 *********************************************************************/

int indexfn(int value, int table[], int max)
{
  int n=0;

  while(1) {
    if (table[n++]==value) return n-1;
    if (n>max) return -1;
  }

}

