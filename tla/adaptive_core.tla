------------------------------ MODULE AdaptiveCore ------------------------------

EXTENDS Naturals, Reals

(*
  This is a minimal formal skeleton.
  It captures:
  - State variables
  - Mode transitions
  - Terminal FALLBACK semantics
  - Core invariants

  It intentionally omits timing granularity and smoothing math.
*)

(* -- Modes ------------------------------------------------------------- *)

Modes == {"STD", "EMG", "CDN", "FBK"}

(* -- State Variables --------------------------------------------------- *)

VARIABLES
    mode,
    energy,
    logical_time

(* -- Constants --------------------------------------------------------- *)

CONSTANTS
    MaxEnergy,
    EmergencyCost

ASSUME MaxEnergy \in Nat
ASSUME EmergencyCost \in Nat

(* -- Initial State ----------------------------------------------------- *)

Init ==
    /\ mode = "STD"
    /\ energy = MaxEnergy
    /\ logical_time = 0

(* -- Transition Relation ---------------------------------------------- *)

Next ==
    \/ (* STANDARD -> EMERGENCY *)
       /\ mode = "STD"
       /\ energy >= EmergencyCost
       /\ mode' = "EMG"
       /\ energy' = energy - EmergencyCost
       /\ logical_time' > logical_time

    \/ (* STANDARD -> FALLBACK *)
       /\ mode = "STD"
       /\ energy < EmergencyCost
       /\ mode' = "FBK"
       /\ energy' = energy
       /\ logical_time' > logical_time

    \/ (* EMERGENCY -> COOLDOWN *)
       /\ mode = "EMG"
       /\ mode' = "CDN"
       /\ energy' = energy
       /\ logical_time' > logical_time

    \/ (* COOLDOWN -> STANDARD *)
       /\ mode = "CDN"
       /\ mode' = "STD"
       /\ energy' <= MaxEnergy
       /\ logical_time' > logical_time

    \/ (* FALLBACK is absorbing *)
       /\ mode = "FBK"
       /\ mode' = "FBK"
       /\ energy' = energy
       /\ logical_time' >= logical_time

(* -- Invariants -------------------------------------------------------- *)

EnergyInvariant ==
    energy >= 0 /\ energy <= MaxEnergy

TerminalFallback ==
    mode = "FBK" => mode' = "FBK"

LogicalTimeInvariant ==
    logical_time >= 0

(* -- Specification ----------------------------------------------------- *)

Spec ==
    Init /\ [][Next]_<<mode, energy, logical_time>>

(* -- Properties -------------------------------------------------------- *)

THEOREM Spec => []EnergyInvariant
THEOREM Spec => []LogicalTimeInvariant

=============================================================================
