/************************************************************************
 *
 *  quant.c, part of tmn (TMN encoder)
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

#include"sim.h"

/**********************************************************************
 *
 *	Name:        Quant
 *	Description:	quantizer for SIM3
 *	
 *	Input:        pointers to coeff and qcoeff
 *        
 *	Returns:	
 *	Side effects:	
 *
 *	Date: 940111	Author:	Karl.Lillevold@nta.no
 *
 ***********************************************************************/


void Quant(int *coeff, int *qcoeff, int QP, int Mode)
{
  int i;
  int level;
  
  if (QP) {
    if (Mode == MODE_INTRA || Mode == MODE_INTRA_Q) { /* Intra */
      qcoeff[0] = mmax(1,mmin(254,coeff[0]/8));

      for (i = 1; i < 64; i++) {
        level = (abs(coeff[i])) / (2*QP);
        qcoeff[i] =  mmin(127,mmax(-127,sign(coeff[i]) * level));
      }
    }
    else { /* non Intra */
      for (i = 0; i < 64; i++) {
        level = (abs(coeff[i])-QP/2)  / (2*QP);
        qcoeff[i] = mmin(127,mmax(-127,sign(coeff[i]) * level));
      }
    }
  }
  else {
    /* No quantizing.
       Used only for testing. Bitstream will not be decodable 
       whether clipping is performed or not */
    for (i = 0; i < 64; i++) {
      qcoeff[i] = coeff[i];
    }
  }
  return;
}

/**********************************************************************
 *
 *	Name:        Dequant
 *	Description:	dequantizer for SIM3
 *	
 *	Input:        pointers to coeff and qcoeff
 *        
 *	Returns:	
 *	Side effects:	
 *
 *	Date: 940111	Author:	Karl.Lillevold@nta.no
 *
 ***********************************************************************/


void Dequant(int *qcoeff, int *rcoeff, int QP, int Mode)
{
  int i;
  
  if (QP) {
    for (i = 0; i < 64; i++) {
      if (qcoeff[i]) {
        if ((QP % 2) == 1)
          rcoeff[i] = QP * (2*abs(qcoeff[i]) + 1);
        else
          rcoeff[i] = QP * (2*abs(qcoeff[i]) + 1) - 1;
        rcoeff[i] = sign(qcoeff[i]) * rcoeff[i];
      }
      else
        rcoeff[i] = 0;
    }
    if (Mode == MODE_INTRA || Mode == MODE_INTRA_Q) { /* Intra */
      rcoeff[0] = qcoeff[0]*8;
    }
  }
  else {
    /* No quantizing at all */
    for (i = 0; i < 64; i++) {
      rcoeff[i] = qcoeff[i];
    }
  }
  return;
}



