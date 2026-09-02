% CEM
% Scattering matrices Transfer matrix method 1D implementation.
% complex impedance (resistive and phase cancellation component)
% complex refractivity
% complex dielectric 
% (diamagnetic vs ferromagnetic vs paramagnetic vs nonmagnetic) - Relative
% Permeability.
% loss tangent
% Duality between E and H fields (usually match)
% E,D,P - H,B,M
% use differential form.  Frequency domain turns convolution of e(t)*E and
% u(t)*H to multiplication. [e]*E, [u]*H
% in the most general sense permeativity e and permeability for anisotropic
% materials is a 3x3 tensor of scalar numbers
% for isotropic its a single scalar identity matrix (really just a single
% scalar)
% frequency domain loses all sense of time (dogma of the circle)
% not enforcing zero divergence creates extra sources in your model and
% this can lead to spurious solutions.
% polarization (LP) vs (CP) vs (EP=elliptical polarization).
% circular polarization we have two components equal in amplitude and 90
% degrees out phase to cause circular polarization.
% there really is no such thing as circular polarization it is just two
% linearly polarized waves that are 90 deg out of phase.
% we will calculate a lot of these polarization vectors for incidences on a
% material.
% Sp x [S11 S12;S21 S22]
function [So] = RedhefferStar(Sp, S11,S12,S21,S22)

    I = eye(2);
    D_s = Sp(:,:,2) / (I - S11*Sp(:,:,4));
    F_s = S21 /(I - Sp(:,:,4)*S11);
    
    So(:,:,1) = Sp(:,:,1) + D_s*S11*Sp(:,:,3);
    So(:,:,2) = D_s*S12;
    So(:,:,3) = F_s*Sp(:,:,3);
    So(:,:,4) = S22+F_s*Sp(:,:,4)*S12;

end

close all;
%% Parameters
lam0 = 0.021;                 % free space wavelength
theta = 45 * pi/180;      % elevation angle of incident wave-front k in radians
phi = 0 * pi/180;        % azimuth angle of incident wave-front k in radians
pte = 1;                  % amplitude of TE polarization (E component of k amplitude).
                          % ay when theta = 0, else n x kinc / | n x kinc |
           
ptm = 1;                  % amplitude of TM polarization (H component of k amplitude).
                          % kinc x pte / | kinc x pte |

ur1 = 1.0;                % permeability in the reflection region
er1 = 1.0;                % permittivity in the reflection region
ur2 = 1.0;                % permeability in the transmission region
er2 = 1.0;                % permittivity in the transmission region



UR = [ 1 3 1];            % array of permeability in each layer.
ER = [ 3 3 3];            % array of permittivity in each layer.
L = [ 0.4 0.8 1.3];       % array of thickness of each layer.
%L = [];
NLYR = length(L);         % number of layers.
linpol = 0;

%% calculate k wave vector (transverse wave vector)
ninc = 1; % refractive index of incident normal of material.
% in the above case n = c/v = 1 means the real speed of the traveling wave
% is the same in the material as it is in the vaccum.  Materials usually
% slow down the wave and change its phase (real part), but the imaginary
% part causes exponential decay term to exist in the equations and that
% causes amplitude degradation or growth for high or very negative values
% of k in n = n+ik.


% NOTE this isnt quite right.  n can be complex and if it is it introduces
% a complex term it causes exponential decay or growth causing the
% dielectric to lose or gain energy.  If it is purely real this doesnt
% happen.

% magnitude of k wave vector |k| = 2*pi / lambda = (2*pi*n) / lam0
magk = (2*pi*ninc) / lam0;

% NOTE this is correct here.
k0 = (2*pi) / lam0; % for clarity I separated these two constants. k0*ninc = magk.

kx = sin(theta)*cos(phi); % this is actually the normalized quantity.
ky = sin(theta)*sin(phi); % this is actually the normalized quantity.
kinc = [magk*kx magk*ky magk*cos(theta)];

%% Calculate gap medium parameters (free space that goes to zero in between layers)
Qg = [ kx*ky 1+ky^2; -(1+kx^2) -kx*ky ];
Vg = -1i*Qg;

%% Initialize Scattering matrix components 
S_glob(:,:,1) = [0 0; 0 0];
S_glob(:,:,2) = [1 0;0 1];
S_glob(:,:,3) = [1 0; 0 1];
S_glob(:,:,4) = [0 0;0 0];

I = eye(2);
kz = zeros(NLYR);
Q = zeros(2,2,NLYR);
Omeg = zeros(2,2,NLYR);
V = zeros(2,2,NLYR);
A = zeros(2,2,NLYR);
B = zeros(2,2,NLYR);
X = zeros(2,2,NLYR);
D = zeros(2,2,NLYR);
S11 = zeros(2,2);
S22 = zeros(2,2);
S12 = zeros(2,2);
S21 = zeros(2,2);

% compute per layer the parameters.
for i=1:NLYR
    kz(i) = sqrt(UR(i)*ER(i) - kx^2 - ky^2);
    Q(:,:,i) = (1/UR(i))*[ kx*ky (UR(i)*ER(i)-kx^2); (ky^2-UR(i)*ER(i)) -kx*ky ];
    Omeg(:,:,i) = 1i*kz(i)*I;
    V(:,:,i) = Q(:,:,i)/(Omeg(:,:,i)); % Q / Omeg.

    A(:,:,i) = I+V(:,:,i)\Vg;
    B(:,:,i) = I-V(:,:,i)\Vg;
    lambda_i = 1i*kz(i);
    X(:,:,i) = [exp(lambda_i*magk*L(i)) 0; 0 exp(lambda_i*magk*L(i))];
    D(:,:,i) = A(:,:,i) - X(:,:,i)*B(:,:,i)/A(:,:,i)*X(:,:,i)*B(:,:,i);
    S11 = D(:,:,i)\(X(:,:,i)*(B(:,:,i)/A(:,:,i))*X(:,:,i)*A(:,:,i)-B(:,:,i));
    S22 = S11;
    S12 = (D(:,:,i)\X(:,:,i))*(A(:,:,i)- ((B(:,:,i)/A(:,:,i))*B(:,:,i)));
    S21 = S12;

    % update global scattering matrix with redheffer star product.
    S_glob = RedhefferStar(S_glob, S11, S12, S12, S22);

    % D_s = S12_glob / (I - S11(:,:,i)*S22_glob);
    % F_s = S21(:,:,i)/(I - S22_glob*S11(:,:,i));
    % 
    % S_glob(:,:,1) = 
    % S11_glob = S11_glob + D_s*S11(:,:,i)*S21_glob;
    % S12_glob = D_s*S12(:,:,i);
    % S21_glob = F_s*S21_glob;
    % S22_glob = S22(:,:,i)+F_s*S22_glob*S12(:,:,i);

end

%% Compute boundaries
kz_ref = sqrt(ur1*er1 - kx^2 - ky^2);
Qref = (1/ur1)*[ kx*ky (ur1*er1-kx^2); (ky^2-ur1*er1) -kx*ky ];
Omegref = 1i*kz_ref*I;
Vref = Qref / Omegref; % Q / Omeg.
Aref = I+Vg\Vref;
Bref = I-Vg\Vref;
S11ref = -1.*(Aref\Bref);
S22ref = Bref/Aref;
S12ref = 2.*inv(Aref);
S21ref = 0.5.*(Aref - (Bref/Aref)*Bref);
Sref = [];
Sref(:,:,1) = S11ref;
Sref(:,:,2) = S12ref;
Sref(:,:,3) = S21ref;
Sref(:,:,4) = S22ref;

S_glob = RedhefferStar(Sref, S_glob(:,:,1), S_glob(:,:,2), S_glob(:,:,3), S_glob(:,:,4));

kz_xmt = sqrt(ur2*er2 - kx^2 - ky^2);
Qxmt = (1/ur2)*[ kx*ky (ur2*er2-kx^2); (ky^2-ur2*er2) -kx*ky ];
Omegxmt = 1i*kz_xmt*I;
Vxmt = Qxmt / Omegxmt; % Q / Omeg.
Axmt = I+Vg\Vxmt;
Bxmt = I-Vg\Vxmt;
S11xmt = Bxmt/Axmt;
S12xmt = 0.5.*(Axmt- (Bxmt/Axmt)*Bxmt);
S21xmt = 2.*inv(Axmt);
S22xmt = -1.*(Axmt\Bxmt);

S_glob = RedhefferStar(S_glob, S11xmt, S12xmt, S21xmt, S22xmt);

%% Compute transverse wave electric and magnetic vectors for linearly polarized wave.
n = [ 0 0 -1];
if(theta == 0)
    ate = [1 0 0];
    atm = [0 1 0];
else
    ate = cross(kinc, n) / norm(cross(kinc, n));
    atm = cross(ate, kinc) / norm(cross(ate, kinc));
end

if linpol == 1
    % linearly polarized calculate electric field using only ate component.
    % can also use atm component and it gives slightly diff values.
    P = ptm.*ate;
    
    % You can construct linearly polarized waves with arbitrary tilt.
    % 45-degree Tilted Linear Polarization this uses the convenience of the
    % magnetic field being 90 degree to electric similar to circular to
    % generate an electric field at a 45degree.
    % E_linear_45 = (1/sqrt(2)) * ate + (1/sqrt(2)) * atm;
    % 

    fprintf("Lin Pol\n")
else % LHCP
    % the transverse electric field ate is perpendicular to k.
    % the transverse magnetic field atm is perpendicular to ate and k
    % we can use this fact to essentially create a circularly polarized
    % wave pretending atm is a perpendicular electric field and phase shift
    % it by 90 degrees via 1i.  Use + for RHCP.
    % 1/sqrt(2) factor is because we want |P|^2 to be 1.  
    P = (1/sqrt(2))*pte.*ate - (1i/sqrt(2))*ptm.*atm;
    fprintf("Circ LH Pol\n")
end

% norm of P should be 1.

esrc = [P(1);P(2)];

eref = S_glob(:,:,1)*esrc;
exmt = S_glob(:,:,3)*esrc;

eref(3) = -(kx*eref(1)+ky*eref(2))/kz_ref;
exmt(3) = -(kx*exmt(1)+ky*exmt(2))/kz_xmt;

R = abs(eref(1))^2 + abs(eref(2))^2 + abs(eref(3))^2
T = (abs(exmt(1))^2 + abs(exmt(2))^2 + abs(exmt(3))^2) * (real(magk*kz_xmt*ur1 / kinc(3)*ur2 ))
% reflectance and transmittance must equal 1 in a lossless dielectric 
% e.g. where n is purely real and k = 0 in n = n+ik 

