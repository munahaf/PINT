import io
import os
from copy import deepcopy

import numpy as np
import pytest

from hypothesis import given
from hypothesis.strategies import (
    composite,
    permutations,
)
from astropy import units as u

from pinttestdata import datadir

from pint import simulation, toa
import pint.residuals
from pint.models import get_model, get_model_and_toas


class TOAOrderSetup:
    parfile = os.path.join(datadir, "NGC6440E.par")
    model = get_model(parfile)
    # fake a multi-telescope, multi-frequency data-set and make sure the results don't depend on TOA order
    fakes = [
        simulation.make_fake_toas_uniform(
            55000, 55500, 30, model=model, freq=1400 * u.MHz, obs="ao"
        ),
        simulation.make_fake_toas_uniform(
            55010, 55500, 40, model=model, freq=800 * u.MHz, obs="gbt"
        ),
        simulation.make_fake_toas_uniform(
            55020, 55500, 50, model=model, freq=2000 * u.MHz, obs="@"
        ),
    ]
    f = io.StringIO()
    for t in fakes:
        t.write_TOA_file(f)
    f.seek(0)
    t = toa.get_TOAs(f)
    r = pint.residuals.Residuals(t, model, subtract_mean=False)

    @classmethod
    @composite
    def toas_and_order(draw, cls):
        # note that draw must come before cls
        n = len(cls.t)
        ix = draw(permutations(np.arange(n)))
        return cls.t, ix


@given(TOAOrderSetup.toas_and_order())
def test_shuffle_toas_residuals_match(t_and_permute):
    toas, ix = t_and_permute
    tcopy = deepcopy(toas)
    tcopy.table = tcopy.table[ix]
    rsort = pint.residuals.Residuals(tcopy, TOAOrderSetup.model, subtract_mean=False)
    assert np.all(TOAOrderSetup.r.time_resids[ix] == rsort.time_resids)


@given(TOAOrderSetup.toas_and_order())
def test_shuffle_toas_chi2_match(t_and_permute):
    toas, ix = t_and_permute
    tcopy = deepcopy(toas)
    tcopy.table = tcopy.table[ix]
    rsort = pint.residuals.Residuals(tcopy, TOAOrderSetup.model, subtract_mean=False)
    # the differences seem to be related to floating point math
    assert np.isclose(TOAOrderSetup.r.calc_chi2(), rsort.calc_chi2(), atol=1e-14)


@pytest.mark.parametrize("sortkey", ["freq", "mjd_float"])
def test_resorting_toas_residuals_match(sortkey):
    tcopy = deepcopy(TOAOrderSetup.t)
    i = np.argsort(TOAOrderSetup.t.table[sortkey])
    tcopy.table = tcopy.table[i]
    rsort = pint.residuals.Residuals(tcopy, TOAOrderSetup.model, subtract_mean=False)
    assert np.all(TOAOrderSetup.r.time_resids[i] == rsort.time_resids)


@pytest.mark.parametrize("sortkey", ["freq", "mjd_float"])
def test_resorting_toas_chi2_match(sortkey):
    tcopy = deepcopy(TOAOrderSetup.t)
    i = np.argsort(TOAOrderSetup.t.table[sortkey])
    tcopy.table = tcopy.table[i]
    rsort = pint.residuals.Residuals(tcopy, TOAOrderSetup.model, subtract_mean=False)
    # the differences seem to be related to floating point math
    assert np.isclose(TOAOrderSetup.r.calc_chi2(), rsort.calc_chi2(), atol=1e-14)
