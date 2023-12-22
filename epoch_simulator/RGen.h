#pragma once
class RGen
{
public:
	RGen(year_TS TS_RGen_1 = {}, year_TS TS_RGen_2 = {}, year_TS TS_RGen_3 = {}, year_TS TS_RGen_4 = {})
		: TS_RGen_1(TS_RGen_1), TS_RGen_2(TS_RGen_2), TS_RGen_3(TS_RGen_3), TS_RGen_4(TS_RGen_4), TS_RGen_total(TS_RGen_total)
	{}

	//Functionality

	void writeTS_RGen_1(year_TS inputTS)
	{
		TS_RGen_1 = inputTS;
		return;
	}

	void writeTS_RGen_2(year_TS inputTS)
	{
		TS_RGen_2 = inputTS;
		return;
	}

	void writeTS_RGen_3(year_TS inputTS)
	{
		TS_RGen_3 = inputTS;
		return;
	}

	void writeTS_RGen_4(year_TS inputTS)
	{
		TS_RGen_4 = inputTS;
		return;
	}
	
	void calculateTS_RGen_total()
	{
		TS_RGen_total = year_TS::add(TS_RGen_1, TS_RGen_2);
		TS_RGen_total = year_TS::add(TS_RGen_total,TS_RGen_3);
		TS_RGen_total = year_TS::add(TS_RGen_total, TS_RGen_4);
		return;
	}

	//Accessor member functions for TS_year

	year_TS getTS_RGen_1()
	{
		return TS_RGen_1;
	}

	year_TS getTS_RGen_2()
	{
		return TS_RGen_2;
	}

	year_TS getTS_RGen_3()
	{
		return TS_RGen_3;
	}

	year_TS getTS_RGen_4()
	{
		return TS_RGen_4;
	}

	year_TS getTS_RGen_total()
	{
		return TS_RGen_total;
	}


private:
	year_TS TS_RGen_1;
	year_TS TS_RGen_2;
	year_TS TS_RGen_3;
	year_TS TS_RGen_4;
	year_TS TS_RGen_total;
	
};

