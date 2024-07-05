COMMENT
:Ornstein-Uhlenbeck process
:http://hines.med.yale.edu/phpBB/viewtopic.php?f=16&t=1308

: 	dn=(-n+u)*dt/tc+s*dWt
:	tc is a time constant
:	u is the mean
:	dWt is the Wiener process
: s is a parameter for the 'noise intensity'.

: Assuming u=0 and s=1/tc 
:    dn/dt=(-n+zt)/tc
:	zt is a normal random variable with mean=0 and some variance
:	n is then just added to the total current
ENDCOMMENT

TITLE Guassian-White noise

NEURON {
	POINT_PROCESS INoise
	RANGE i, std, tau, bias, del, dur, x
	ELECTRODE_CURRENT i
}

UNITS {
	(nA) = (nanoamp)
}

PARAMETER {
	bias = 0 (nA)
	std = 0   (nA)

	del	= 0    (ms)
	dur = 0   (ms)
	x = 0
}

ASSIGNED {
	i (nA)
	iamp (nA)
	noise (nA)
	on (1)
}


INITIAL {
	i = 0
	iamp = 0
}

STATE {
	n (nA) 
}

PROCEDURE seed(x) {
	set_seed(x)
}

BREAKPOINT {
	at_time(del)
	at_time(del+dur)
	
	SOLVE kin METHOD cnexp
	
	if (t<del+dur && t>=del) { 
		: iamp = bias 
		iamp = bias + noise
	} else {
		iamp = 0
	}
	
	i = iamp

}

DERIVATIVE kin {
	noise = normrand(0,std*1(/nA))*1(nA)
	n' = (-n + noise)
	: n' = (-n + noise)
}