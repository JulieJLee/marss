/************************************************************************
 *
 *  putbits.c, bitstream handling for tmn (TMN encoder)
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

/************************************************************************
 *  Based on functions in the MPEG-2 software encoder by the
 *  MPEG-2 Software Simulation Group, modified by
 *
 *  Robert Danielsen, <Robert.Danielsen@nta.no>
 ************************************************************************/
 

#include "sim.h"

extern FILE *streamfile; /* the only global var we need here */

/* private data */
static unsigned char outbfr;
static int outcnt;
static int bytecnt;

/* initialize buffer, call once before first putbits or alignbits */
void
initbits()
{
  outcnt = 8;
  bytecnt = 0;
}

/* write rightmost n (0<=n<=32) bits of val to outfile */

void
putbits (int n, int val)
{
  int i;
  unsigned int mask;
  char bitstring[32];

  if (trace) {
    if (n > 0) {
      BitPrint(n,val,bitstring);
      fprintf(tf,bitstring);
    }
  }

  mask = 1 << (n-1); /* selects first (leftmost) bit */

  for (i=0; i<n; i++) {
    outbfr <<= 1;

    if (val & mask)
      outbfr|= 1;

    mask >>= 1; /* select next bit */
    outcnt--;

    if (outcnt==0) /* 8 bit buffer full */ {
      putc(outbfr,streamfile);
      outcnt = 8;
      bytecnt++;
    }
  }
}


/* zero bit stuffing to next byte boundary (5.2.3, 6.2.1) */

int
alignbits ()
{
  int ret_value;
  
  if (outcnt!=8) {
    ret_value = outcnt;	/* outcnt is reset in call to putbits () */
    putbits (outcnt, 0);
    return ret_value;
  }
  else
    return 0;
}

/* return total number of generated bits */
int
bitcount()
{
  return 8*bytecnt + (8-outcnt);
}

/* convert to binary number */
void 
BitPrint(int length, int val, char *bit)
{
  int m;
  
  m = length;
  bit[0] = '"';
  while (m--) {
    bit[length-m] = (val & (1<<m)) ? '1' : '0';
  }
  bit[length+1] = '"';
  bit[length+2] = '\n';
  bit[length+3] = '\0';
  return;
}

